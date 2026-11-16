import unittest

from simple_text_table import Column, Table, render
from simple_text_table.core import display_width


class DisplayWidthTests(unittest.TestCase):
    def test_ascii(self):
        self.assertEqual(display_width("abc"), 3)

    def test_empty(self):
        self.assertEqual(display_width(""), 0)

    def test_cjk_is_two_cells(self):
        # U+4E2D is East Asian Wide.
        self.assertEqual(display_width("\u4e2d"), 2)

    def test_hangul_is_two_cells(self):
        # U+AC00 is East Asian Wide.
        self.assertEqual(display_width("\uac00"), 2)

    def test_combining_mark_is_zero(self):
        # "e" followed by U+0301 COMBINING ACUTE ACCENT.
        self.assertEqual(display_width("e\u0301"), 1)

    def test_mixed(self):
        self.assertEqual(display_width("a\u4e2db"), 4)


class PadTests(unittest.TestCase):
    def test_left_pad_ascii(self):
        from simple_text_table.core import _pad
        self.assertEqual(_pad("ab", 5, "left"), "ab   ")

    def test_right_pad_ascii(self):
        from simple_text_table.core import _pad
        self.assertEqual(_pad("ab", 5, "right"), "   ab")

    def test_center_pad_ascii(self):
        from simple_text_table.core import _pad
        self.assertEqual(_pad("ab", 6, "center"), "  ab  ")

    def test_center_pad_odd_gap(self):
        from simple_text_table.core import _pad
        # gap of 3 -> left 1, right 2
        self.assertEqual(_pad("ab", 5, "center"), " ab  ")

    def test_pad_wide_char(self):
        from simple_text_table.core import _pad
        # "\u4e2d" is 2 cells, pad to 5 -> 3 spaces
        self.assertEqual(_pad("\u4e2d", 5, "left"), "\u4e2d   ")

    def test_pad_no_gap(self):
        from simple_text_table.core import _pad
        self.assertEqual(_pad("abc", 3, "left"), "abc")

    def test_pad_negative_gap_returns_text(self):
        from simple_text_table.core import _pad
        self.assertEqual(_pad("abc", 1, "left"), "abc")

    def test_unknown_alignment_raises(self):
        from simple_text_table.core import _pad
        with self.assertRaises(ValueError):
            _pad("a", 3, "middle")


class TableTests(unittest.TestCase):
    def test_simple_render(self):
        table = Table([Column("name"), Column("age", "right")])
        table.add_row("alice", "30")
        table.add_row("bob", "7")
        expected = (
            "name  | age\n"
            "------+----\n"
            "alice |  30\n"
            "bob   |   7\n"
        )
        self.assertEqual(table.render(), expected)

    def test_wide_characters_align(self):
        table = Table([Column("word"), Column("n", "right")])
        table.add_row("\u4e2d\u6587", "2")
        table.add_row("hi", "1")
        # "\u4e2d\u6587" is 4 cells wide, "word" is 4 cells wide.
        expected = (
            "word | n\n"
            "-----+--\n"
            "\u4e2d\u6587 | 2\n"
            "hi   | 1\n"
        )
        self.assertEqual(table.render(), expected)

    def test_combining_mark_does_not_inflate_width(self):
        table = Table([Column("word")])
        table.add_row("e\u0301")
        # "e\u0301" is one display cell, so the column is 4 cells wide
        # because of the header "word", leaving a gap of 3 spaces.
        expected = "word\n----\ne\u0301   \n"
        self.assertEqual(table.render(), expected)

    def test_short_row_is_padded_with_empty(self):
        table = Table([Column("a"), Column("b"), Column("c")])
        table.add_row("1")
        expected = (
            "a | b | c\n"
            "--+---+--\n"
            "1 |   |  \n"
        )
        self.assertEqual(table.render(), expected)

    def test_long_row_raises(self):
        table = Table([Column("a")])
        with self.assertRaises(ValueError):
            table.add_row("1", "2")

    def test_center_alignment(self):
        table = Table([Column("h", "center")])
        table.add_row("x")
        expected = (
            "h\n"
            "-\n"
            "x\n"
        )
        self.assertEqual(table.render(), expected)

    def test_center_alignment_pads(self):
        table = Table([Column("header", "center")])
        table.add_row("x")
        expected = (
            "header\n"
            "------\n"
            "  x   \n"
        )
        self.assertEqual(table.render(), expected)

    def test_empty_table_renders_header_only(self):
        table = Table([Column("a"), Column("b")])
        expected = (
            "a | b\n"
            "--+--\n"
        )
        self.assertEqual(table.render(), expected)

    def test_add_row_returns_self(self):
        table = Table([Column("a")])
        self.assertIs(table.add_row("1"), table)

    def test_render_function(self):
        out = render(
            [Column("k"), Column("v", "right")],
            [["a", "1"], ["bb", "22"]],
        )
        expected = (
            "k  |  v\n"
            "---+---\n"
            "a  |  1\n"
            "bb | 22\n"
        )
        self.assertEqual(out, expected)

    def test_non_string_cells_are_stringified(self):
        table = Table([Column("n")])
        table.add_row(42)
        self.assertIn("42", table.render())


if __name__ == "__main__":
    unittest.main()
