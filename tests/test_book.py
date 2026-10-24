from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.book import check_links, navigation_changes, parse_document, replace_block  # noqa: E402


class MarkdownTests(unittest.TestCase):
    def test_heading_punctuation_and_duplicates(self):
        doc = parse_document("# Tools & equipment\n## Again\n## Again\n## Again-1\n")
        self.assertEqual(doc.anchors, {"tools--equipment", "again", "again-1", "again-1-1"})
        self.assertEqual(doc.errors, [])

    def test_custom_anchors_and_code_fences(self):
        doc = parse_document('<a id="stable"></a>\n## Visible\n```md\n# Hidden\n[bad](missing.md)\n```\n[ok](#stable)')
        self.assertEqual(doc.anchors, {"stable", "visible"})
        self.assertEqual(doc.links, [(7, "#stable")])
        self.assertEqual(doc.errors, [])

    def test_duplicate_explicit_anchor_and_unclosed_fence(self):
        self.assertTrue(parse_document('<a id="same"></a>\n## Same').errors)
        self.assertTrue(parse_document("```python\npass").errors)

    def test_inline_code_is_not_a_link(self):
        self.assertEqual(parse_document("`[fake](missing.md)` and [real](ok.md)").links, [(1, "ok.md")])

    def test_reference_links(self):
        doc = parse_document("[read][guide]\n[guide][]\n[guide]\n[guide]: target.md#start\n")
        self.assertFalse(doc.errors)
        self.assertEqual(doc.links, [(1, "target.md#start"), (2, "target.md#start"), (3, "target.md#start")])
        self.assertEqual(parse_document("[unused]: nowhere.md\n").links, [])
        self.assertTrue(parse_document("[read][undefined]").errors)

    def test_navigation_markers_must_be_unique(self):
        with self.assertRaisesRegex(ValueError, "one pair"):
            replace_block("no markers", "NAV", "content")

    def test_nested_links_fragments_case_and_reachability(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "chapters").mkdir()
            (root / "README.MD").write_text("# Book\n[chapter](chapters/one.md#stable)\n")
            chapter = root / "chapters/one.md"
            chapter.write_text('<a id="stable"></a>\n# One\n[home](../README.MD#book)\n')
            self.assertEqual(check_links(root)[0], [])
            chapter.write_text(chapter.read_text() + "[bad](../README.MD#missing)\n")
            self.assertTrue(any("fragment does not exist" in error for error in check_links(root)[0]))
            chapter.write_text(chapter.read_text() + "[outside](../../outside.md)\n")
            self.assertTrue(any("path leaves repository" in error for error in check_links(root)[0]))
            (root / "orphan.md").write_text("# Orphan\n")
            self.assertTrue(any("unreachable" in error for error in check_links(root)[0]))

    def test_angle_destination_and_percent_encoded_fragment(self):
        doc = parse_document('[spaced](<a file.md#an%20anchor>)')
        self.assertEqual(doc.links, [(1, "a file.md#an%20anchor")])

    def test_repository_navigation_is_current(self):
        self.assertEqual(navigation_changes(ROOT), {})

    def test_repository_links_are_valid(self):
        errors, documents, links = check_links(ROOT)
        self.assertEqual(errors, [])
        self.assertGreaterEqual(documents, 20)
        self.assertGreater(links, 200)


if __name__ == "__main__":
    unittest.main()
