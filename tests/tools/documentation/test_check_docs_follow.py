# test_check_docs_follow.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the checker of the pages a commit leaves behind, on a temporary git repository whose pages follow a fact."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock


from sushicore.tools.documentation import check_docs_follow, docs_follow  # noqa: E402
from tests.tools.documentation.fact_pages import K_FOLLOW, K_HOME  # noqa: E402


class TestFollowOnDisk(unittest.TestCase):
    """Runs the collection of commits and the rule on a git repository of a home and a page."""
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

    def _git(self, *arguments: str) -> str:
        identity = ["-c", "user.name=Test", "-c", "user.email=test@example.com",
                    "-c", "commit.gpgsign=false"]
        return subprocess.run(["git", "-C", str(self.root), *identity, *arguments],
                              check=True, capture_output=True, text=True).stdout

    def _commit(self, message: str) -> None:
        self._git("add", "-A")
        self._git("commit", "-q", "-m", message)

    def _start_repository(self) -> None:
        """Makes a git repository of a home and a page, as the base of the follow tests."""
        self._git("init", "-q")
        self.write("home.md", K_HOME)
        self.write("follow.md", K_FOLLOW)
        self._commit("start")
        self.base = self._git("rev-parse", "HEAD").strip()

    def _follow_problems(self) -> list[str]:
        with mock.patch.object(docs_follow, "K_SINCE", self.base):
            return [issue.message for commit in check_docs_follow.collect([self.root])
                    for issue in check_docs_follow.rule_pages_follow(commit)]

    def test_the_followers_page_in_the_commit_satisfies_the_rule(self) -> None:
        self._start_repository()
        self.write("home.md", K_HOME.replace("last phase", "final phase"))
        self.write("follow.md", K_FOLLOW + "Checked.\n")
        self._commit("change the fact")
        self.assertEqual(self._follow_problems(), [])

    def test_a_docs_line_satisfies_the_rule(self) -> None:
        self._start_repository()
        self.write("home.md", K_HOME.replace("last phase", "final phase"))
        self._commit("change the fact\n\nDocs: follow.md unchanged (the paraphrase still holds)")
        self.assertEqual(self._follow_problems(), [])

    def test_editing_text_outside_the_fact_is_free(self) -> None:
        self._start_repository()
        self.write("home.md", K_HOME + "\nMore text outside the fact.\n")
        self._commit("edit around the fact")
        self.assertEqual(self._follow_problems(), [])

    def test_a_commit_that_changes_the_fact_and_leaves_the_follower_is_reported(self) -> None:
        self._start_repository()
        self.write("home.md", K_HOME.replace("last phase", "final phase"))
        self._commit("change the fact")
        problems = self._follow_problems()
        self.assertEqual(len(problems), 1)
        self.assertIn("follow.md follows the fact shipping", problems[0])

    def test_a_path_that_is_not_a_folder_yields_no_commit(self) -> None:
        self._start_repository()
        with mock.patch.object(docs_follow, "K_SINCE", self.base):
            self.assertEqual(check_docs_follow.collect([self.root / "home.md"]), [])


if __name__ == "__main__":
    unittest.main()
