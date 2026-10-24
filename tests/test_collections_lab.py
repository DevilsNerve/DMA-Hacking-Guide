from __future__ import annotations

import codecs
from contextlib import redirect_stdout
import io
from pathlib import Path
import struct
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from labs.advanced_lab import Snapshot, decode  # noqa: E402
from labs.collections_lab import (  # noqa: E402
    TEXT_SAMPLES, TraversalError, array_first, decoder_cases, layout_cases,
    main, text_image, walk_chain,
)


class CollectionTextTests(unittest.TestCase):
    def test_literal_text_encodings_and_preserved_labels(self):
        expected = {"ascii": (1, 1, 1, "4100"), "precomposed": (1, 1, 2, "e900"),
                    "combining": (2, 2, 3, "65000103"), "compass": (1, 2, 4, "3ed8eddd"),
                    "embedded-nul": (3, 3, 3, "410000004200"),
                    "leading-feff": (2, 2, 4, "fffe4100")}
        for name, label in TEXT_SAMPLES:
            with self.subTest(name=name):
                points, units, utf8, raw = expected[name]
                self.assertEqual((len(label), len(label.encode("utf-8"))), (points, utf8))
                self.assertEqual(label.encode("utf-16-le").hex(), raw)
                self.assertEqual(decode(text_image(bytes.fromhex(raw), units)).label, label)

    def test_successful_wrong_endian_decode_does_not_identify_encoding(self):
        raw = bytes.fromhex("3ed8eddd")
        self.assertEqual(raw.decode("utf-16-le"), "\U0001f9ed")
        self.assertEqual([ord(char) for char in raw.decode("utf-16-be")], [0x3ED8, 0xEDDD])

    def test_incremental_chunks_and_strict_finalization(self):
        decoder = codecs.getincrementaldecoder("utf-16-le")(errors="strict")
        self.assertEqual([decoder.decode(bytes.fromhex(raw), final=False)
                          for raw in ("3e", "d8ed", "dd")], ["", "", "\U0001f9ed"])
        self.assertEqual(decoder.decode(b"", final=True), "")
        for raw in ("3e", "3ed8", "3ed8ed"):
            with self.subTest(raw=raw):
                decoder = codecs.getincrementaldecoder("utf-16-le")(errors="strict")
                self.assertEqual(decoder.decode(bytes.fromhex(raw), final=False), "")
                with self.assertRaises(UnicodeDecodeError):
                    decoder.decode(b"", final=True)

    def test_alternative_layouts_and_literal_field_positions(self):
        self.assertTrue(all(row["equal"] for row in layout_cases()))
        data = array_first()
        self.assertEqual(len(data), 96)
        self.assertEqual(struct.unpack_from("<II", data, 24), (80, 32))
        self.assertEqual(data[32:48].hex(), "0a0000000000af420000803f00000040")
        self.assertEqual(data[68:72], bytes.fromhex("00004842"))  # Third health: 50.
        self.assertEqual(data[80:96].hex(), "500069006c006f00740020003ed8eddd")

    def test_casebook_validations_and_failure_exit(self):
        cases = decoder_cases()
        self.assertEqual(len(cases), 25)
        self.assertTrue(all(row["passed"] for row in cases))
        self.assertEqual(sum(row["outcome"] == "accepted" for row in cases), 9)
        with patch("labs.collections_lab.decode", return_value=Snapshot("", 0, ())), redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(["cases"]), 1)
        self.assertIn("FAIL duplicate-id accepted", output.getvalue())


class ChainTests(unittest.TestCase):
    def test_complete_chain_and_exact_budget(self):
        self.assertEqual(walk_chain((1, 2, -1), 0, 3), (0, 1, 2))
        self.assertEqual(walk_chain((1, 2, -1), 2, 1), (2,))
        self.assertEqual(walk_chain((), -1, 0), ())
        with self.assertRaisesRegex(TraversalError, "budget exhausted"):
            walk_chain((1, 2, -1), 0, 2)

    def test_cycle_and_invalid_links_remain_distinct(self):
        for links, message in (((1, 0), "cycle at index 0"), ((0,), "cycle at index 0"),
                               ((3, -1), "index out of range: 3"), ((-2,), "index out of range: -2"),
                               ((False,), "must be an integer")):
            with self.subTest(links=links), self.assertRaisesRegex(TraversalError, message):
                walk_chain(links, 0, 4)

    def test_bounded_inputs_and_invalid_start(self):
        for start in (True, 0.0, "0", -2, 1):
            with self.subTest(start=start), self.assertRaises(TraversalError):
                walk_chain((-1,), start, 1)
        for budget in (-1, True, 1.5, 1025):
            with self.subTest(budget=budget), self.assertRaises(TraversalError):
                walk_chain((-1,), 0, budget)
        with self.assertRaises(TraversalError):
            walk_chain(tuple([-1] * 1025), -1, 0)
        self.assertEqual(walk_chain(tuple(range(1, 1024)) + (-1,), 0, 1024), tuple(range(1024)))


class CollectionsCliTests(unittest.TestCase):
    def test_documented_commands(self):
        chapter = (ROOT / "chapters/15-strings-and-collections.md").read_text(encoding="utf-8")
        for command in ("text", "cases", "layouts", "traversal"):
            with self.subTest(command=command):
                result = subprocess.run([sys.executable, str(ROOT / "labs/collections_lab.py"), command],
                                        capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)
                if command in ("layouts", "traversal"):
                    self.assertIn(result.stdout.strip(), chapter)
                elif command == "text":
                    self.assertIn("\n".join(result.stdout.splitlines()[-4:]), chapter)
                else:
                    self.assertIn(result.stdout.splitlines()[-1], chapter)


if __name__ == "__main__":
    unittest.main()
