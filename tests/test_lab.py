from __future__ import annotations

from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from labs.memory_lab import (  # noqa: E402
    DEFAULT_PATTERN, FAULTS, Image, LabError, MAX_IMAGE,
    create_fixture, decode, find_pattern, load_image,
)


class DecodeTests(unittest.TestCase):
    def test_known_bytes_and_observations_for_both_widths(self):
        for bits, base in ((32, 0x400000), (64, 0x140000000)):
            with self.subTest(bits=bits):
                image = create_fixture(bits)
                self.assertEqual(image.base, base)
                self.assertEqual(len(image.data), 512)
                self.assertEqual(image.data[0x100:0x114].hex(),
                                 "444d414c01002000020000000000af4203000000")
                self.assertEqual(image.data[0x180:0x186].hex(), "0a0014001e00")
                observation = decode(image)
                self.assertEqual(observation.address, base + 0x100)
                self.assertEqual(observation.health, 87.5)
                self.assertEqual(observation.items, (10, 20, 30))
                self.assertEqual(observation.sequence, 2)

    def test_known_pointer_representation(self):
        image = create_fixture()
        self.assertEqual(image.data[0x40:0x48].hex(), "0001004001000000")
        self.assertEqual(image.data[0x114:0x11C].hex(), "8001004001000000")

    def test_all_documented_faults_for_both_widths(self):
        expected = {
            "null-root": "null root pointer", "bad-magic": "magic mismatch",
            "bad-version": "unsupported record version", "bad-size": "size mismatch",
            "bad-count": "item count exceeds", "odd-sequence": "inconsistent sequence",
            "mismatched-sequence": "inconsistent sequence", "nan-health": "invalid health",
            "dangling-items": "unavailable range", "truncated": "unavailable range",
        }
        self.assertEqual(set(expected), set(FAULTS))
        for bits in (32, 64):
            for fault, message in expected.items():
                with self.subTest(bits=bits, fault=fault), self.assertRaisesRegex(LabError, message):
                    decode(create_fixture(bits, fault))

    def test_zero_count_is_valid_without_dereferencing_null(self):
        image = create_fixture()
        data = bytearray(image.data)
        data[0x110:0x11C] = bytes(12)
        self.assertEqual(decode(Image(bytes(data), image.base)).items, ())

    def test_nonempty_array_requires_pointer(self):
        image = create_fixture()
        data = bytearray(image.data)
        data[0x114:0x11C] = bytes(8)
        with self.assertRaisesRegex(LabError, "null item pointer"):
            decode(Image(bytes(data), image.base))

    def test_health_boundaries_and_nonfinite_values(self):
        image = create_fixture()
        for value, valid in ((0, True), (100, True), (-1, False), (101, False),
                             (float("inf"), False), (float("-inf"), False)):
            with self.subTest(value=value):
                data = bytearray(image.data)
                struct.pack_into("<f", data, 0x10C, value)
                changed = Image(bytes(data), image.base)
                if valid:
                    self.assertEqual(decode(changed).health, value)
                else:
                    with self.assertRaisesRegex(LabError, "invalid health"):
                        decode(changed)

    def test_width_mismatch_fails(self):
        for source, target in ((64, 32), (32, 64)):
            with self.subTest(source=source, target=target), self.assertRaises(LabError):
                decode(Image(create_fixture(source).data, create_fixture(target).base, target))

    def test_exact_read_bounds(self):
        image = Image(b"ABCD", 0x1000, 32)
        self.assertEqual(image.read_exact(0x1001, 3), b"BCD")
        for address, length in ((0xFFF, 1), (0x1003, 2), (0x1000, -1),
                                (0x1000, MAX_IMAGE + 1), (1 << 32, 1), (0xFFFFFFFF, 2)):
            with self.subTest(address=address, length=length), self.assertRaises(LabError):
                image.read_exact(address, length)

    def test_image_range_and_size_limits(self):
        for data, base, bits in ((b"12", 0xFFFFFFFF, 32), (b"", -1, 64),
                                 (b"", 0, 16), (bytes(MAX_IMAGE + 1), 0, 64)):
            with self.subTest(base=base, bits=bits), self.assertRaises(LabError):
                Image(data, base, bits)

    def test_file_limit_enforced_on_read(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "large.bin"
            path.write_bytes(bytes(MAX_IMAGE + 1))
            with self.assertRaisesRegex(LabError, "1 MiB"):
                load_image(path, 64)


class PatternTests(unittest.TestCase):
    def test_every_chunk_size_preserves_boundary_matches(self):
        data = b"xxABCxxABCxABC"
        for chunk in range(1, len(data) + 2):
            with self.subTest(chunk=chunk):
                self.assertEqual(find_pattern(data, "41 ?? 43", chunk), [2, 7, 11])

    def test_overlapping_matches(self):
        self.assertEqual(find_pattern(b"AAAA", "41 41", 1), [0, 1, 2])

    def test_single_byte_does_not_duplicate(self):
        self.assertEqual(find_pattern(b"AAAA", "41", 1), [0, 1, 2, 3])

    def test_fixture_signature(self):
        self.assertEqual(find_pattern(create_fixture().data, DEFAULT_PATTERN, 7), [0x100])

    def test_zero_matches_and_empty_input(self):
        self.assertEqual(find_pattern(b"ABC", "DE AD"), [])
        self.assertEqual(find_pattern(b"", "41"), [])

    def test_invalid_patterns(self):
        for pattern in ("", "??", "? ??", "ZZ", "0x41", "4", "41 " * 129):
            with self.subTest(pattern=pattern), self.assertRaises(LabError):
                find_pattern(b"ABC", pattern)

    def test_invalid_chunks_and_match_limit(self):
        for chunk in (0, -1, MAX_IMAGE + 1):
            with self.subTest(chunk=chunk), self.assertRaises(LabError):
                find_pattern(b"ABC", "41", chunk)
        with self.assertRaisesRegex(LabError, "match count"):
            find_pattern(b"A" * 1025, "41")


class CliTests(unittest.TestCase):
    def run_cli(self, *args, cwd=None):
        return subprocess.run([sys.executable, str(ROOT / "labs/memory_lab.py"), *args],
                              cwd=cwd, capture_output=True, text=True, timeout=10)

    def test_documented_demo(self):
        result = self.run_cli("demo")
        self.assertEqual(result.returncode, 0, result.stderr)
        expected = ("pointer_bits=64 base=0x140000000\n"
                    "record=0x140000100 sequence=2\n"
                    "health=87.5 items=[10, 20, 30]\n"
                    "signature_matches=['0x140000100']\n")
        self.assertEqual(result.stdout, expected)
        self.assertIn(expected.strip(), (ROOT / "labs/README.md").read_text(encoding="utf-8"))
        self.assertIn(expected.strip(), (ROOT / "chapters/03-tools-and-lab.md").read_text(encoding="utf-8"))

    def test_create_inspect_scan_and_overwrite_policy(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "space ü" / "fixture.bin")
            self.assertEqual(self.run_cli("create", path, "--bits", "32").returncode, 0)
            read = self.run_cli("inspect", path, "--bits", "32")
            self.assertEqual(read.returncode, 0, read.stderr)
            self.assertIn("record=0x400100", read.stdout)
            scan = self.run_cli("scan", path, "--bits", "32", "--chunk-size", "7")
            self.assertEqual(scan.stdout, "signature_matches=['0x400100']\n")
            original = Path(path).read_bytes()
            self.assertEqual(self.run_cli("create", path).returncode, 1)
            self.assertEqual(Path(path).read_bytes(), original)
            self.assertEqual(self.run_cli("create", path, "--fault", "null-root", "--force").returncode, 0)
            failure = self.run_cli("inspect", path)
            self.assertEqual(failure.returncode, 1)
            self.assertEqual(failure.stdout, "")
            self.assertIn("null root pointer", failure.stderr)

    def test_missing_file_and_bad_options(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(self.run_cli("inspect", str(Path(directory) / "missing.bin")).returncode, 1)
        self.assertEqual(self.run_cli("demo", "--bits", "16").returncode, 2)


if __name__ == "__main__":
    unittest.main()
