from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from labs.deep_dive import MappingError, SECTIONS, Section, map_range, trace  # noqa: E402


class SectionMappingTests(unittest.TestCase):
    def test_complete_ranges_and_exact_raw_boundary(self):
        for rva, length, expected in ((0x1250, 4, 0x650), (0x13F8, 8, 0x7F8),
                                      (0x2100, 16, 0x900), (0x21F8, 8, 0x9F8)):
            with self.subTest(rva=rva, length=length):
                self.assertEqual(map_range(SECTIONS, 4096, rva, length), expected)

    def test_incomplete_raw_ranges_and_virtual_only_sections(self):
        for rva, length in ((0x13F8, 16), (0x1450, 4), (0x3000, 1), (0x21F8, 9)):
            with self.subTest(rva=rva), self.assertRaisesRegex(MappingError, "stored counterpart"):
                map_range(SECTIONS, 4096, rva, length)

    def test_unmapped_gap_and_cross_section_request(self):
        for rva, length in ((0x1800, 4), (0x15FF, 2), (0x100, 1)):
            with self.subTest(rva=rva), self.assertRaisesRegex(MappingError, "no section"):
                map_range(SECTIONS, 4096, rva, length)

    def test_overlapping_metadata_is_rejected_even_for_other_request(self):
        overlapping = SECTIONS + (Section("overlap", 0x2100, 0x100, 0xB00, 0x100),)
        with self.assertRaisesRegex(MappingError, "overlapping"):
            map_range(overlapping, 4096, 0x1250, 4)

    def test_truncated_file_rejected_before_mapping(self):
        with self.assertRaisesRegex(MappingError, "raw range exceeds file"):
            map_range(SECTIONS, 0x900, 0x1250, 4)

    def test_integer_width_empty_request_and_section_budget(self):
        for rva, length in ((-1, 4), (1 << 32, 4), (0x1250, 0),
                             (0xFFFFFFFF, 2), (0x1250, True), (0x1250, 1.5)):
            with self.subTest(rva=rva, length=length), self.assertRaises(MappingError):
                map_range(SECTIONS, 4096, rva, length)
        for sections in ((), SECTIONS * 33,
                         (replace(SECTIONS[0], rva=0xFFFFFF00),),
                         (replace(SECTIONS[0], virtual_size=0),),
                         (replace(SECTIONS[0], raw_at=-1),)):
            with self.subTest(sections=sections), self.assertRaises(MappingError):
                map_range(sections, 4096, 0x1250, 4)
        self.assertEqual(map_range((Section("last-byte", 0xFFFFFFFF, 1, 0, 1),),
                                   1, 0xFFFFFFFF, 1), 0)


class DeepDiveEvidenceTests(unittest.TestCase):
    def test_every_replay_state_transition(self):
        rows = trace()
        self.assertEqual([row["accepted_generation"] for row in rows], [2, 2, 2, 2, 4, 4, 4, 4])
        self.assertEqual([row["last_progress_ms"] for row in rows], [0, 0, 0, 0, 40, 40, 40, 40])
        self.assertEqual([row["last_observation_ms"] for row in rows], [0, 10, 20, 30, 40, 50, 60, 200])

    def test_documented_commands_and_fixture_hashes(self):
        guide = (ROOT / "labs/advanced.md").read_text(encoding="utf-8")
        for command in ("sections", "precision", "trace", "evidence"):
            with self.subTest(command=command):
                result = subprocess.run([sys.executable, str(ROOT / "labs/deep_dive.py"), command],
                                        capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)
                if command != "evidence":
                    self.assertIn(result.stdout.rstrip(), guide)
                if command == "sections":
                    self.assertEqual(result.stdout.count(" rejected:"), 3)
                    self.assertIn("rva=0x13f8 length=8 file=0x7f8", result.stdout)
                elif command == "precision":
                    self.assertIn("1.health:0.100000001->0.100000009", result.stdout)
                elif command == "trace":
                    self.assertIn("200 no-progress 4 200 40", result.stdout)
                else:
                    report = json.loads(result.stdout)
                    expected = {
                        "before": (96, "6ba403a2af1c2058b0dd4f7a13f93ef3a47d50cebc71bff8f9ea29bf54161b2e"),
                        "relocated": (112, "2f542a573c7d33f461e78fdd8680b83dd9cf5dd9c23e340feb9bfe3584cff346"),
                        "after": (112, "ab9cc8774ccc34f8d73044e0caeb4c9896334d825a4059f598d89085346378d1"),
                    }
                    for case, (size, digest) in expected.items():
                        self.assertEqual(report["fixtures"][case]["bytes"], size)
                        self.assertEqual(report["fixtures"][case]["sha256"], digest)
                    self.assertEqual(report["before_to_relocated"][-1], "changed=[]")
                    self.assertEqual(report["replay"][-1]["last_progress_ms"], 40)


if __name__ == "__main__":
    unittest.main()
