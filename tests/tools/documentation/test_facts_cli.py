# test_facts_cli.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the facts command: the places that cite a fact, the rewrite it plans and its subcommands on a tree."""

from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path


from sushicore.tools.documentation import facts_cli  # noqa: E402
from tests.tools.documentation.fact_pages import K_FOLLOW, K_HOME, K_QUOTE, manual_of  # noqa: E402


class TestCitations(unittest.TestCase):
    """Covers which places the command lists for a fact, from manuals built in memory."""
    K_TEST_SIZE = "small"

    def test_citations_list_quotes_and_follows_in_page_order(self) -> None:
        manual = manual_of({"quote.md": K_QUOTE, "follow.md": K_FOLLOW})
        self.assertEqual(
            facts_cli.citations(manual, "shipping"),
            ["quote.md:3: quote", "follow.md:3: follows"],
        )

    def test_every_quote_of_a_fact_is_listed(self) -> None:
        manual = manual_of({"a.md": K_QUOTE, "b.md": K_QUOTE})
        self.assertEqual(len(facts_cli.citations(manual, "shipping")), 2)

    def test_citations_skip_the_quotes_of_other_facts(self) -> None:
        manual = manual_of({"quote.md": K_QUOTE, "other.md": K_QUOTE.replace("shipping", "other")})
        self.assertEqual(facts_cli.citations(manual, "shipping"), ["quote.md:3: quote"])

    def test_an_uncited_fact_has_no_citations(self) -> None:
        self.assertEqual(facts_cli.citations(manual_of({"home.md": K_HOME}), "shipping"), [])


class TestPlanApply(unittest.TestCase):
    """Covers which pages the rewrite changes, and with what text, before anything is written."""
    K_TEST_SIZE = "small"

    def test_a_stale_quote_is_planned_with_its_new_text(self) -> None:
        stale = K_QUOTE.replace("last phase", "final phase")
        manual = manual_of({"home.md": K_HOME, "page.md": stale})
        self.assertEqual(facts_cli.plan_apply(manual), [("page.md", K_QUOTE)])

    def test_pages_with_current_quotes_are_not_planned(self) -> None:
        manual = manual_of({"home.md": K_HOME, "page.md": K_QUOTE, "other.md": "# Other\n"})
        self.assertEqual(facts_cli.plan_apply(manual), [])

    def test_planning_a_planned_text_again_plans_nothing(self) -> None:
        stale = K_QUOTE.replace("last phase", "final phase")
        first = facts_cli.plan_apply(manual_of({"home.md": K_HOME, "page.md": stale}))
        again = manual_of({"home.md": K_HOME, "page.md": first[0][1]})
        self.assertEqual(facts_cli.plan_apply(again), [])

    def test_planned_pages_keep_their_order(self) -> None:
        stale = K_QUOTE.replace("last phase", "final phase")
        manual = manual_of({"home.md": K_HOME, "b.md": stale, "a.md": stale})
        self.assertEqual([page for page, _ in facts_cli.plan_apply(manual)], ["b.md", "a.md"])


class TestCommand(unittest.TestCase):
    """Runs each subcommand on tiny trees in temporary folders."""
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

    def _run(self, *arguments: str) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = facts_cli.main(["--root", str(self.root), *arguments])
        return code, out.getvalue()

    def test_cited_by_lists_every_quote_and_follow(self) -> None:
        self.write("home.md", K_HOME)
        self.write("quote.md", K_QUOTE)
        self.write("follow.md", K_FOLLOW)
        code, output = self._run("cited-by", "shipping")
        self.assertEqual(code, 0)
        self.assertEqual(sorted(output.splitlines()), ["follow.md:3: follows", "quote.md:3: quote"])

    def test_where_names_the_home(self) -> None:
        self.write("home.md", K_HOME)
        self.write("quote.md", K_QUOTE)
        self.assertEqual(self._run("where", "shipping")[1].strip(), "home.md:3")

    def test_list_names_the_home_and_the_citations(self) -> None:
        self.write("home.md", K_HOME)
        self.write("quote.md", K_QUOTE)
        self.assertEqual(self._run("list")[1].strip(), "shipping: home.md:3, cited 1")

    def test_an_unknown_id_is_an_error(self) -> None:
        self.assertEqual(self._run("cited-by", "nothing")[0], 1)

    def test_apply_rewrites_a_stale_quote(self) -> None:
        self.write("home.md", K_HOME)
        self.write("page.md", K_QUOTE.replace("last phase", "final phase"))
        self.assertEqual(self._run("apply")[1].strip(), "page.md: written")
        self.assertEqual((self.root / "page.md").read_text(encoding="utf-8"), K_QUOTE)

    def test_a_second_apply_writes_nothing(self) -> None:
        self.write("home.md", K_HOME)
        self.write("page.md", K_QUOTE.replace("last phase", "final phase"))
        self._run("apply")
        self.assertEqual(self._run("apply")[1], "")

    def test_apply_refuses_a_stale_page_that_is_not_utf8_and_writes_nothing(self) -> None:
        self.write("home.md", K_HOME)
        bad = b"# Bad\n\xff\n<!-- quote:begin shipping -->\nold\n<!-- quote:end shipping -->\n"
        (self.root / "bad.md").write_bytes(bad)
        with self.assertRaises(UnicodeDecodeError):
            self._run("apply")
        self.assertEqual((self.root / "bad.md").read_bytes(), bad)


if __name__ == "__main__":
    unittest.main()
