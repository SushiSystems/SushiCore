# test_facts.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the facts core on values in memory: how the markers of a page are read and how a quote is rewritten."""

from __future__ import annotations

import unittest


from sushicore.tools.documentation import facts  # noqa: E402
from tests.tools.documentation.fact_pages import K_FOLLOW, K_HOME, K_QUOTE  # noqa: E402


class TestParsing(unittest.TestCase):
    """Covers how the markers of one page are read, from text in memory."""
    K_TEST_SIZE = "small"

    def test_a_fact_has_its_id_lines_and_body(self) -> None:
        block = facts.parse("a.md", K_HOME).facts[0]
        self.assertEqual((block.id, block.first, block.last), ("shipping", 3, 5))
        self.assertEqual(block.body, "A topic ships when its last phase is built.")

    def test_a_multi_line_fact_keeps_every_line_of_its_body(self) -> None:
        text = "<!-- fact:begin x -->\nfirst\nsecond\n<!-- fact:end x -->\n"
        self.assertEqual(facts.parse("a.md", text).facts[0].body, "first\nsecond")

    def test_an_empty_fact_has_an_empty_body(self) -> None:
        text = "<!-- fact:begin x -->\n<!-- fact:end x -->\n"
        self.assertEqual(facts.parse("a.md", text).facts[0].body, "")

    def test_a_quote_is_found(self) -> None:
        self.assertEqual(facts.parse("a.md", K_QUOTE).quotes[0].id, "shipping")

    def test_a_follow_mark_is_found_with_its_line(self) -> None:
        self.assertEqual(facts.parse("a.md", K_FOLLOW).follows, [("shipping", 3)])

    def test_a_follow_mark_inside_a_fact_is_body_text(self) -> None:
        text = "<!-- fact:begin x -->\n<!-- follows: y -->\n<!-- fact:end x -->\n"
        page = facts.parse("a.md", text)
        self.assertEqual((page.follows, page.facts[0].body), ([], "<!-- follows: y -->"))

    def test_a_well_formed_page_has_no_faults(self) -> None:
        self.assertEqual(facts.parse("a.md", K_HOME + K_QUOTE + K_FOLLOW).faults, [])

    def test_a_fact_never_closed_is_a_fault(self) -> None:
        found = facts.parse("a.md", "<!-- fact:begin x -->\ntext\n").faults
        self.assertIn("never closed", found[0][1])

    def test_an_end_without_its_beginning_is_a_fault(self) -> None:
        found = facts.parse("a.md", "<!-- fact:end x -->\n").faults
        self.assertIn("without its beginning", found[0][1])

    def test_an_end_with_another_id_is_a_fault(self) -> None:
        self.assertTrue(facts.parse("a.md", "<!-- fact:begin x -->\n<!-- fact:end y -->\n").faults)

    def test_a_quote_end_that_closes_a_fact_is_a_fault(self) -> None:
        self.assertTrue(facts.parse("a.md", "<!-- fact:begin x -->\n<!-- quote:end x -->\n").faults)

    def test_a_marker_inside_another_block_is_a_fault(self) -> None:
        nested = ("<!-- fact:begin x -->\n<!-- quote:begin y -->\n"
                  "<!-- quote:end y -->\n<!-- fact:end x -->\n")
        self.assertIn("begins inside", facts.parse("a.md", nested).faults[0][1])

    def test_crlf_text_is_read_the_same_as_lf(self) -> None:
        self.assertEqual(
            facts.parse("a.md", K_HOME.replace("\n", "\r\n")).facts,
            facts.parse("a.md", K_HOME).facts,
        )


class TestRegeneration(unittest.TestCase):
    """Covers how a quote is rewritten from the body of its home."""
    K_TEST_SIZE = "small"

    def test_regenerate_replaces_only_the_quote_bodies(self) -> None:
        stale = K_QUOTE.replace("last phase is built", "old text")
        home = {"shipping": "A topic ships when its last phase is built."}
        self.assertEqual(facts.regenerate(stale, home), K_QUOTE)

    def test_regenerate_keeps_crlf_and_unknown_quotes(self) -> None:
        crlf = K_QUOTE.replace("\n", "\r\n")
        self.assertEqual(facts.regenerate(crlf, {}), crlf)

    def test_regenerate_rewrites_every_stale_quote_of_a_page(self) -> None:
        stale = K_QUOTE.replace("last phase is built", "old text")
        home = {"shipping": "A topic ships when its last phase is built."}
        self.assertEqual(facts.regenerate(stale + stale, home), K_QUOTE + K_QUOTE)

    def test_an_empty_home_empties_the_quote(self) -> None:
        self.assertEqual(
            facts.regenerate(K_QUOTE, {"shipping": ""}),
            "# Page\n\n<!-- quote:begin shipping -->\n<!-- quote:end shipping -->\n",
        )

    def test_a_multi_line_home_replaces_the_body_with_all_its_lines(self) -> None:
        self.assertEqual(
            facts.regenerate(K_QUOTE, {"shipping": "one\ntwo"}),
            "# Page\n\n<!-- quote:begin shipping -->\none\ntwo\n<!-- quote:end shipping -->\n",
        )


if __name__ == "__main__":
    unittest.main()
