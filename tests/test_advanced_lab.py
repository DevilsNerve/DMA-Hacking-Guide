from __future__ import annotations

from dataclasses import replace
import hashlib
import math
from pathlib import Path
import random
import re
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from labs.advanced_lab import (  # noqa: E402
    DecodeError, Entity, ReplayMonitor, Snapshot, compare, decode, encode,
    make_case, read_file, replay_events, semantic_view,
)

CHANGED = ("generations=2->4\nlabel_changed=no\nadded=[30] removed=[40]\n"
           "changed=['10.health:87.5->60', '20.y:12->13']\n")
UNCHANGED = "generations=2->2\nlabel_changed=no\nadded=[] removed=[]\nchanged=[]\n"
DEMO = ("label='Pilot \\U0001f9ed' generation=2 entities=3\nids=[10, 20, 40]\n"
        "id=10 health=87.5 x=1 y=2\nid=20 health=100 x=10 y=12\n"
        "id=40 health=50 x=-1 y=3\n" + CHANGED)
REPLAY = ("  0 ms accepted\n 10 ms duplicate\n 20 ms unavailable\n 30 ms invalid\n"
          " 40 ms accepted\n 50 ms regressed\n 60 ms inconsistent\n200 ms no-progress\n")


class AdvancedDecodeTests(unittest.TestCase):
    def test_independently_specified_bytes(self):
        data = make_case("before")
        self.assertEqual(len(data), 96)
        self.assertEqual(data[:32].hex(), "4f42533202002000020000000000000003000000080000002000000030000000")
        self.assertEqual(data[32:48].hex(), "500069006c006f00740020003ed8eddd")
        self.assertEqual(data[48:64].hex(), "0a0000000000af420000803f00000040")
        result = decode(data)
        self.assertEqual(result, Snapshot("Pilot \U0001f9ed", 2,
                         (Entity(10, 87.5, 1, 2), Entity(20, 100, 10, 12), Entity(40, 50, -1, 3))))

    def test_text_unit_boundaries_and_embedded_null(self):
        for text in ("", "A" * 64, "\U0001f9ed" * 32, "a\x00b", "e\u0301", "\u4e2d\u6587"):
            with self.subTest(text=ascii(text)):
                self.assertEqual(decode(encode(Snapshot(text, 0, ()))).label, text)
        for text in ("A" * 65, "\U0001f9ed" * 33, "\ud800"):
            with self.subTest(text=ascii(text)), self.assertRaises(DecodeError):
                encode(Snapshot(text, 0, ()))

    def test_entity_count_boundaries(self):
        for count in (0, 1, 64):
            with self.subTest(count=count):
                snapshot = Snapshot("", 7, tuple(Entity(i + 1, 0, 0, 0) for i in range(count)))
                self.assertEqual(len(decode(encode(snapshot)).entities), count)
        changed = bytearray(make_case("before"))
        struct.pack_into("<I", changed, 16, 65)
        with self.assertRaisesRegex(DecodeError, "count"):
            decode(bytes(changed))

    def test_invalid_header_and_image_limits(self):
        baseline = make_case("before")
        for data in (b"", baseline[:31], baseline + bytes(4097), b"XXXX" + baseline[4:]):
            with self.subTest(size=len(data)), self.assertRaises(DecodeError):
                decode(data)
        for offset, value in ((4, 3), (6, 31)):
            data = bytearray(baseline)
            struct.pack_into("<H", data, offset, value)
            with self.subTest(offset=offset), self.assertRaises(DecodeError):
                decode(bytes(data))

    def test_name_count_and_isolated_surrogate(self):
        baseline = make_case("before")
        data = bytearray(baseline)
        struct.pack_into("<I", data, 20, 65)
        with self.assertRaisesRegex(DecodeError, "name length"):
            decode(bytes(data))
        data = bytearray(baseline)
        struct.pack_into("<I", data, 20, 1)
        data[32:34] = b"\x00\xd8"
        with self.assertRaisesRegex(DecodeError, "malformed UTF-16"):
            decode(bytes(data))

    def test_payload_ranges_and_overlap(self):
        for offset, value, message in ((24, 16, "range"), (24, 0xFFFFFFFF, "range"),
                                      (28, 0xFFFFFFFF, "range"), (28, 32, "overlap")):
            data = bytearray(make_case("before"))
            struct.pack_into("<I", data, offset, value)
            with self.subTest(offset=offset, value=value), self.assertRaisesRegex(DecodeError, message):
                decode(bytes(data))

    def test_required_byte_truncation_and_optional_padding(self):
        data = make_case("before")
        with self.assertRaisesRegex(DecodeError, "range"):
            decode(data[:-1])
        self.assertEqual(decode(data), decode(data + bytes(17)))

    def test_exact_image_limit_and_empty_payload_positions(self):
        baseline = make_case("before")
        at_limit = baseline + bytes(4096 - len(baseline))
        self.assertEqual(decode(at_limit), decode(baseline))
        with self.assertRaisesRegex(DecodeError, "image size"):
            decode(at_limit + b"\x00")
        empty = bytes.fromhex("4f42533202002000000000000000000000000000000000002000000020000000")
        self.assertEqual(decode(empty), Snapshot("", 0, ()))
        wrong_empty_offset = empty[:28] + bytes(4)
        with self.assertRaisesRegex(DecodeError, "range"):
            decode(wrong_empty_offset)

    def test_literal_surrogate_pair_and_array_before_name(self):
        compass = bytes.fromhex("4f425332020020000000000000000000000000000200000020000000240000003ed8eddd")
        self.assertEqual(decode(compass), Snapshot("\U0001f9ed", 0, ()))
        header = bytes.fromhex("4f42533202002000020000000000000001000000010000003000000020000000")
        record = bytes.fromhex("0a0000000000af420000803f00000040")
        self.assertEqual(decode(header + record + b"A\x00"),
                         Snapshot("A", 2, (Entity(10, 87.5, 1, 2),)))

    def test_duplicate_and_zero_identifiers(self):
        for position, identifier in ((48, 0), (64, 10)):
            data = bytearray(make_case("before"))
            struct.pack_into("<I", data, position, identifier)
            with self.subTest(identifier=identifier), self.assertRaisesRegex(DecodeError, "unique"):
                decode(bytes(data))

    def test_finite_fields_and_health_range(self):
        for offset, value in ((52, float("nan")), (56, float("inf")), (60, float("-inf")),
                              (52, -1), (52, 101)):
            data = bytearray(make_case("before"))
            struct.pack_into("<f", data, offset, value)
            with self.subTest(offset=offset, value=value), self.assertRaises(DecodeError):
                decode(bytes(data))

    def test_file_input_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "oversize.obs"
            path.write_bytes(bytes(4097))
            with self.assertRaisesRegex(DecodeError, "4096"):
                read_file(path)

    def test_fixed_seed_mutations_have_controlled_outcomes(self):
        rng = random.Random(19020)
        baseline = make_case("before")
        accepted = rejected = 0
        for number in range(512):
            changed = bytearray(baseline)
            for _ in range(rng.randint(1, 4)):
                changed[rng.randrange(len(changed))] = rng.randrange(256)
            with self.subTest(case=number, seed=19020):
                try:
                    result = decode(bytes(changed))
                except DecodeError:
                    rejected += 1
                else:
                    accepted += 1
                    self.assertLessEqual(len(result.label.encode("utf-16-le")) // 2, 64)
                    self.assertLessEqual(len(result.entities), 64)
                    ids = [item.identifier for item in result.entities]
                    self.assertEqual(len(ids), len(set(ids)))
                    self.assertNotIn(0, ids)
                    for item in result.entities:
                        self.assertTrue(all(math.isfinite(value) for value in (item.health, item.x, item.y)))
                        self.assertTrue(0 <= item.health <= 100)
        self.assertGreater(accepted, 0)
        self.assertGreater(rejected, 0)

    def test_arbitrary_bytes_have_controlled_outcomes(self):
        rng = random.Random(19021)
        for number in range(128):
            data = bytes(rng.randrange(256) for _ in range(rng.randrange(300)))
            with self.subTest(case=number, seed=19021):
                try:
                    decode(data)
                except DecodeError:
                    pass


class ComparisonTests(unittest.TestCase):
    def test_distinct_binary32_values_have_distinct_reported_values(self):
        left = struct.unpack("<f", bytes.fromhex("cdcccc3d"))[0]
        right = struct.unpack("<f", bytes.fromhex("cecccc3d"))[0]
        before = decode(encode(Snapshot("", 1, (Entity(1, left, 0, 0),))))
        after = decode(encode(Snapshot("", 2, (Entity(1, right, 0, 0),))))
        self.assertNotEqual(left, right)
        self.assertEqual(compare(before, after).changed, ("1.health:0.100000001->0.100000009",))
        for value in (left, right):
            self.assertEqual(struct.pack("<f", float(f"{value:.9g}")), struct.pack("<f", value))

    def test_relocation_and_reordering_preserve_meaning(self):
        before, moved = make_case("before"), make_case("relocated")
        self.assertNotEqual(hashlib.sha256(before).digest(), hashlib.sha256(moved).digest())
        self.assertEqual(len(moved), 112)
        self.assertNotEqual(decode(before).entities, decode(moved).entities)
        self.assertEqual(semantic_view(decode(before)), semantic_view(decode(moved)))
        self.assertEqual("\n".join(compare(decode(before), decode(moved)).lines()) + "\n", UNCHANGED)

    def test_known_semantic_changes(self):
        result = compare(decode(make_case("before")), decode(make_case("after")))
        self.assertEqual("\n".join(result.lines()) + "\n", CHANGED)

    def test_label_change_and_numeric_signed_zero_policy(self):
        before = Snapshot("old", 1, (Entity(1, 0.0, 1, 2),))
        after = Snapshot("new", 2, (Entity(1, -0.0, 1, 2),))
        result = compare(decode(encode(before)), decode(encode(after)))
        self.assertTrue(result.label_changed)
        self.assertEqual(result.changed, ())


class ReplayTests(unittest.TestCase):
    def test_complete_trace_and_retained_state(self):
        monitor = ReplayMonitor()
        statuses = [monitor.observe(time, data) for time, data in replay_events()]
        self.assertEqual(statuses, ["accepted", "duplicate", "unavailable", "invalid", "accepted",
                                    "regressed", "inconsistent", "no-progress"])
        self.assertEqual(monitor.accepted, decode(make_case("after")))
        self.assertEqual(monitor.last_progress_ms, 40)
        self.assertEqual(monitor.last_observation_ms, 200)

    def test_budget_boundary_and_relocated_duplicate(self):
        monitor = ReplayMonitor()
        self.assertEqual(monitor.observe(0, make_case("before")), "accepted")
        self.assertEqual(monitor.observe(100, make_case("relocated")), "duplicate")
        self.assertEqual(monitor.observe(101, make_case("before")), "no-progress")
        self.assertEqual(monitor.last_progress_ms, 0)

    def test_failures_before_first_valid_sample(self):
        monitor = ReplayMonitor()
        self.assertEqual(monitor.observe(0, None), "unavailable")
        self.assertEqual(monitor.observe(1, b""), "invalid")
        self.assertIsNone(monitor.accepted)
        self.assertIsNone(monitor.last_progress_ms)
        self.assertEqual(monitor.observe(2, make_case("before")), "accepted")

    def test_invalid_clock_and_budget(self):
        for value in (-1, 1.5, float("nan"), True):
            with self.subTest(budget=value), self.assertRaises(ValueError):
                ReplayMonitor(value)
        monitor = ReplayMonitor()
        for value in (-1, 1.5, float("nan"), True):
            with self.subTest(time=value), self.assertRaises(ValueError):
                monitor.observe(value, None)
        monitor.observe(10, make_case("before"))
        with self.assertRaises(ValueError):
            monitor.observe(9, make_case("after"))
        self.assertEqual(monitor.last_progress_ms, 10)

    def test_generation_rollover_requires_new_session(self):
        top = encode(Snapshot("", (1 << 64) - 1, ()))
        zero = encode(Snapshot("", 0, ()))
        monitor = ReplayMonitor()
        self.assertEqual(monitor.observe(0, top), "accepted")
        self.assertEqual(monitor.observe(1, zero), "regressed")
        self.assertEqual(ReplayMonitor().observe(0, zero), "accepted")


class AdvancedCliTests(unittest.TestCase):
    def cli(self, *args):
        return subprocess.run([sys.executable, str(ROOT / "labs/advanced_lab.py"), *args],
                              capture_output=True, text=True, timeout=10)

    def test_documented_demo_and_replay(self):
        guide = (ROOT / "labs/advanced.md").read_text(encoding="utf-8")
        for command, expected in (("demo", DEMO), ("replay", REPLAY)):
            with self.subTest(command=command):
                result = self.cli(command)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, expected)
                self.assertIn(expected.rstrip(), guide)

    def test_file_workflow_and_no_partial_report(self):
        with tempfile.TemporaryDirectory() as directory:
            paths = {case: Path(directory) / "space ü" / f"{case}.obs" for case in ("before", "relocated", "after")}
            for case, path in paths.items():
                result = self.cli("create", str(path), "--case", case)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(hashlib.sha256(path.read_bytes()).hexdigest(), result.stdout)
                self.assertEqual(self.cli("inspect", str(path)).returncode, 0)
            for case, expected in (("relocated", UNCHANGED), ("after", CHANGED)):
                result = self.cli("compare", str(paths["before"]), str(paths[case]))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, expected)
                self.assertIn(expected.rstrip(), (ROOT / "chapters/20-complete-investigation.md").read_text(encoding="utf-8"))
            original = paths["before"].read_bytes()
            self.assertEqual(self.cli("create", str(paths["before"])).returncode, 1)
            self.assertEqual(paths["before"].read_bytes(), original)
            self.assertEqual(self.cli("create", str(paths["before"]), "--force").returncode, 0)
            paths["after"].write_bytes(b"invalid")
            failure = self.cli("compare", str(paths["before"]), str(paths["after"]))
            self.assertEqual(failure.returncode, 1)
            self.assertEqual(failure.stdout, "")

    def test_missing_file_and_invalid_command(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(self.cli("inspect", str(Path(directory) / "missing.obs")).returncode, 1)
        self.assertEqual(self.cli("create", "unused.obs", "--case", "unknown").returncode, 2)

    def test_inspection_keeps_binary32_precision(self):
        value = struct.unpack("<f", bytes.fromhex("cecccc3d"))[0]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "precision.obs"
            path.write_bytes(encode(Snapshot("", 1, (Entity(1, value, 0, 0),))))
            result = self.cli("inspect", str(path))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("health=0.100000009", result.stdout)

    def test_chapter_python_examples(self):
        examples = (("15-strings-and-collections.md", "7 8 16\nTrue\n"),
                    ("16-modules-and-symbols.md", "0x650\n"))
        for filename, expected in examples:
            source = (ROOT / "chapters" / filename).read_text(encoding="utf-8")
            snippets = re.findall(r"```python\n(.*?)\n```", source, re.S)
            self.assertEqual(len(snippets), 1)
            result = subprocess.run([sys.executable, "-c", snippets[0]], capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, expected)


if __name__ == "__main__":
    unittest.main()
