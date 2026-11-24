# test_check_docs_facts.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the checker of the facts a manual keeps in one home: its four rules, the pages it reads and its run on a tree."""

from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path


from sushicore.tools.documentation import check_docs_facts  # noqa: E402
from tests.tools.documentation.fact_pages import K_FOLLOW, K_HOME, K_QUOTE, K_ROOT, manual_of  # noqa: E402


def _messages(rule, pages: dict[str, str]) -> list[str]:
    """Returns the message of each issue the rule finds in the given pages."""
    return [issue.message for issue in rule(manual_of(pages))]


class TestRules(unittest.TestCase):
    """Covers the four rules of the facts checker, on manuals built in memory."""
    K_TEST_SIZE = "small"

    def test_a_current_quote_passes_every_rule(self) -> None:
        pages = {"home.md": K_HOME, "page.md": K_QUOTE + K_FOLLOW}
        for rule in check_docs_facts.K_CHECKER.rules.values():
            self.assertEqual(_messages(rule, pages), [])

    def test_a_stale_quote_names_its_home_and_the_command(self) -> None:
        pages = {"home.md": K_HOME, "page.md": K_QUOTE.replace("last phase", "final phase")}
        message = _messages(check_docs_facts.rule_quote_current, pages)[0]
        self.assertIn("home.md", message)
        self.assertIn("facts_cli apply", message)

    def test_a_quote_whose_fact_has_no_home_is_left_to_the_existence_rule(self) -> None:
        self.assertEqual(_messages(check_docs_facts.rule_quote_current, {"page.md": K_QUOTE}), [])

    def test_two_homes_for_one_id_are_refused(self) -> None:
        found = _messages(check_docs_facts.rule_unique_ids, {"a.md": K_HOME, "b.md": K_HOME})
        self.assertEqual(len(found), 1)

    def test_one_id_twice_on_one_page_is_refused(self) -> None:
        found = _messages(check_docs_facts.rule_unique_ids, {"a.md": K_HOME + K_HOME})
        self.assertEqual(len(found), 1)

    def test_a_quote_or_follow_of_a_missing_fact_is_refused(self) -> None:
        found = _messages(check_docs_facts.rule_cited_fact_exists, {"page.md": K_QUOTE + K_FOLLOW})
        self.assertEqual(len(found), 2)

    def test_a_follow_of_a_missing_fact_names_the_fact(self) -> None:
        pages = {"page.md": "<!-- follows: ghost -->\ntext\n"}
        found = _messages(check_docs_facts.rule_cited_fact_exists, pages)
        self.assertEqual(found, ["follows ghost, which has no home"])

    def test_a_home_on_the_quoting_page_satisfies_the_quote(self) -> None:
        pages = {"page.md": K_HOME + K_QUOTE}
        self.assertEqual(_messages(check_docs_facts.rule_cited_fact_exists, pages), [])

    def test_faulty_markers_are_reported(self) -> None:
        found = _messages(check_docs_facts.rule_markers, {"page.md": "<!-- fact:begin x -->\n"})
        self.assertEqual(len(found), 1)

    def test_a_marker_fault_is_reported_on_its_line(self) -> None:
        manual = manual_of({"page.md": "text\n<!-- fact:end x -->\n"})
        issues = list(check_docs_facts.rule_markers(manual))
        self.assertEqual(issues[0].line, 2)

    def test_the_first_home_of_an_id_is_the_one_kept(self) -> None:
        manual = manual_of({"a.md": K_HOME, "b.md": K_HOME.replace("built", "shipped")})
        self.assertEqual(manual.homes()["shipping"][0].path, "a.md")

    def test_a_quote_is_not_a_home(self) -> None:
        self.assertEqual(manual_of({"page.md": K_QUOTE}).homes(), {})


class TestPageSelection(unittest.TestCase):
    """Covers which pages the manual reads and the names it gives them, from paths in memory."""
    K_TEST_SIZE = "small"

    def test_build_folders_are_skipped(self) -> None:
        self.assertFalse(check_docs_facts.is_checked_page(K_ROOT, K_ROOT / "build" / "a.md"))

    def test_third_party_and_dependency_folders_are_skipped(self) -> None:
        third_party = K_ROOT / "docs" / "third_party" / "b.md"
        self.assertFalse(check_docs_facts.is_checked_page(K_ROOT, third_party))
        self.assertFalse(check_docs_facts.is_checked_page(K_ROOT, K_ROOT / "node_modules" / "c.md"))

    def test_ordinary_folders_are_checked(self) -> None:
        guide = K_ROOT / "docs" / "guides" / "d.md"
        self.assertTrue(check_docs_facts.is_checked_page(K_ROOT, guide))

    def test_page_paths_are_relative_and_posix(self) -> None:
        self.assertEqual(manual_of({"docs/guides/a.md": K_HOME}).pages[0].path, "docs/guides/a.md")


class TestChecker(unittest.TestCase):
    """Runs the checker on tiny trees in temporary folders."""
    K_TEST_SIZE = "medium"

    def setUp(self) -> None:
        self._folder = tempfile.TemporaryDirectory()
        self.root = Path(self._folder.name)

    def tearDown(self) -> None:
        self._folder.cleanup()

    def write(self, name: str, text: str) -> None:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="")

    def test_the_checker_passes_a_clean_tree(self) -> None:
        self.write("home.md", K_HOME)
        self.write("page.md", K_QUOTE)
        self.assertEqual(self._check(), (0, ""))

    def test_the_checker_names_a_stale_quote(self) -> None:
        self.write("home.md", K_HOME)
        self.write("page.md", K_QUOTE.replace("last phase", "final phase"))
        code, output = self._check()
        self.assertEqual(code, 1)
        self.assertIn("rule_quote_current", output)
        self.assertIn("facts_cli apply", output)

    def _check(self) -> tuple[int, str]:
        """Returns the exit code and the printed findings of the checker run on the tree."""
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = check_docs_facts.run(check_docs_facts.K_CHECKER, [str(self.root)])
        return code, out.getvalue()


if __name__ == "__main__":
    unittest.main()
