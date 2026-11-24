# test_source_blanking.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests blanking the comments and strings of C-family source and finding the brace that closes a block."""

from __future__ import annotations

import unittest


from sushicore.tools.testing.source_blanking import blank, matching_brace  # noqa: E402


def _blank(text: str, backtick: bool = False, raw: bool = False) -> str:
    """Returns the text blanked with the given string forms."""
    return blank(text, backtick=backtick, raw=raw)


class BlankTest(unittest.TestCase):
    """Covers which characters turn into spaces and which stay."""
    K_TEST_SIZE = "small"

    def test_a_line_comment_is_blanked_up_to_the_newline(self) -> None:
        self.assertEqual(_blank("a // b {\nc"), "a" + " " * 7 + "\nc")

    def test_a_block_comment_is_blanked_and_its_newlines_stay(self) -> None:
        self.assertEqual(_blank("a /* {\n} */ b"), "a" + " " * 5 + "\n" + " " * 5 + "b")

    def test_an_unterminated_block_comment_is_blanked_to_the_end(self) -> None:
        self.assertEqual(_blank("a /* b"), "a     ")

    def test_the_inside_of_a_string_is_blanked_and_its_quotes_stay(self) -> None:
        self.assertEqual(_blank('x = "a{b" + y'), 'x = "   " + y')

    def test_an_escaped_quote_does_not_end_a_string(self) -> None:
        self.assertEqual(_blank(r'"a\"{" {'), '"    " {')

    def test_a_character_literal_is_blanked(self) -> None:
        self.assertEqual(_blank("c = '{' ;"), "c = ' ' ;")

    def test_a_comment_marker_inside_a_string_is_text_not_a_comment(self) -> None:
        self.assertEqual(_blank('"//" x'), '"  " x')

    def test_a_quote_inside_a_comment_opens_no_string(self) -> None:
        self.assertEqual(_blank("// \" \nx {"), "   " + "  \nx {")

    def test_a_backtick_string_is_blanked_only_when_asked(self) -> None:
        self.assertEqual(_blank("`a{b`", backtick=True), "`   `")
        self.assertEqual(_blank("`a{b`"), "`a{b`")

    def test_a_raw_string_is_blanked_between_its_delimiters_when_asked(self) -> None:
        self.assertEqual(_blank('R"x(a{)"b)x" {', raw=True), 'R"x(' + " " * 5 + ')x" {')

    def test_a_raw_string_with_a_quote_inside_hides_its_brace_only_when_asked(self) -> None:
        text = 'R"(a"b{)"'
        self.assertNotIn("{", _blank(text, raw=True))
        self.assertIn("{", _blank(text))

    def test_an_r_that_ends_a_name_is_no_raw_string_prefix(self) -> None:
        text = 'fooR"(a{b)"'
        self.assertEqual(_blank(text, raw=True), 'fooR"     "')

    def test_the_result_keeps_the_length_of_the_text(self) -> None:
        text = 'int a; // c\n/* d */ char *s = "e\\"f"; R"y(g)y"\n'
        self.assertEqual(len(_blank(text, raw=True)), len(text))


class MatchingBraceTest(unittest.TestCase):
    """Covers finding the brace that closes the one at an offset."""
    K_TEST_SIZE = "small"

    def test_the_closing_brace_of_a_flat_block_is_found(self) -> None:
        self.assertEqual(matching_brace("{ a }", 0), 4)

    def test_a_nested_block_does_not_close_the_outer_one(self) -> None:
        code = "{ { } x }"
        self.assertEqual(matching_brace(code, 0), 8)
        self.assertEqual(matching_brace(code, 2), 4)

    def test_a_block_that_never_closes_has_no_match(self) -> None:
        self.assertIsNone(matching_brace("{ { }", 0))

    def test_braces_that_blanking_hid_are_not_counted(self) -> None:
        code = _blank('{ "}" /* } */ }')
        self.assertEqual(matching_brace(code, 0), len(code) - 1)


if __name__ == "__main__":
    unittest.main()
