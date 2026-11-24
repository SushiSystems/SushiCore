# test_tooling_bridge.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests how the checkers find the tooling package that owns the backlog and design rules, and run them."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


from sushicore.tools.documentation import tooling_bridge  # noqa: E402

K_PACKAGE = "bridgefixture_pkg"


class TestLoad(unittest.TestCase):
    """Covers finding a module of the tooling package, installed or in a checkout beside the repository."""
    K_TEST_SIZE = "medium"

    def setUp(self) -> None:
        self._folder = tempfile.TemporaryDirectory()
        self.base = Path(self._folder.name)
        self.root = self.base / "repository"
        self.root.mkdir()
        self._path = list(sys.path)

    def tearDown(self) -> None:
        sys.path[:] = self._path
        for name in [name for name in sys.modules if name.split(".")[0] == K_PACKAGE]:
            del sys.modules[name]
        self._folder.cleanup()

    def _checkout(self) -> None:
        """Writes a checkout of the fixture package, with one module, beside the repository."""
        package = self.base / "checkout" / K_PACKAGE
        package.mkdir(parents=True)
        (package / "__init__.py").write_text("", encoding="utf-8")
        (package / "design.py").write_text("K_MARK = 'sibling'\n", encoding="utf-8")

    def test_a_repository_that_names_no_package_loads_nothing(self) -> None:
        with mock.patch.object(tooling_bridge, "K_PACKAGE", ""):
            self.assertIsNone(tooling_bridge.load("design", self.root))

    def test_an_installed_package_is_imported(self) -> None:
        module = tooling_bridge.load("design", Path(__file__).resolve().parents[3])
        self.assertEqual(module.__name__, "sushicore.design")

    def test_a_package_that_is_nowhere_loads_nothing(self) -> None:
        with (mock.patch.object(tooling_bridge, "K_PACKAGE", K_PACKAGE),
              mock.patch.object(tooling_bridge, "K_SIBLING_SOURCE", "")):
            self.assertIsNone(tooling_bridge.load("design", self.root))

    def test_a_checkout_beside_the_repository_is_put_on_the_path_and_imported(self) -> None:
        self._checkout()
        with (mock.patch.object(tooling_bridge, "K_PACKAGE", K_PACKAGE),
              mock.patch.object(tooling_bridge, "K_SIBLING_SOURCE", "checkout")):
            module = tooling_bridge.load("design", self.root)
        self.assertEqual(module.K_MARK, "sibling")

    def test_a_named_checkout_that_does_not_exist_loads_nothing(self) -> None:
        with (mock.patch.object(tooling_bridge, "K_PACKAGE", K_PACKAGE),
              mock.patch.object(tooling_bridge, "K_SIBLING_SOURCE", "absent")):
            self.assertIsNone(tooling_bridge.load("design", self.root))
        self.assertEqual(sys.path, self._path)


class TestMissing(unittest.TestCase):
    """Covers the issue that says the rules of a module could not run."""
    K_TEST_SIZE = "small"

    def test_without_a_package_the_issue_names_the_setting(self) -> None:
        with mock.patch.object(tooling_bridge, "K_PACKAGE", ""):
            issue = tooling_bridge.missing(Path("docs"), "design")
        self.assertIn("sets no K_TOOLING_PACKAGE", issue.message)

    def test_with_a_package_the_issue_names_it_and_the_minimum_version(self) -> None:
        with (mock.patch.object(tooling_bridge, "K_PACKAGE", "acme"),
              mock.patch.object(tooling_bridge, "K_MINIMUM_VERSION", "1.2.3")):
            issue = tooling_bridge.missing(Path("docs"), "design")
        self.assertEqual(issue.message, "acme.design is not importable; install acme 1.2.3 or later to run these rules")

    def test_without_a_minimum_version_the_issue_asks_for_the_package_alone(self) -> None:
        with (mock.patch.object(tooling_bridge, "K_PACKAGE", "acme"),
              mock.patch.object(tooling_bridge, "K_MINIMUM_VERSION", "")):
            issue = tooling_bridge.missing(Path("docs"), "backlog")
        self.assertTrue(issue.message.endswith("install acme to run these rules"))

    def test_the_issue_sits_on_the_given_path_at_line_one(self) -> None:
        issue = tooling_bridge.missing(Path("docs/design"), "design")
        self.assertEqual((issue.path, issue.line), (Path("docs/design"), 1))


class TestDesignRule(unittest.TestCase):
    """Covers the rule that runs one design rule of the tooling package."""
    K_TEST_SIZE = "small"

    ROOT = Path("repo")

    @staticmethod
    def _design(findings: list) -> SimpleNamespace:
        """Returns a stand-in design module whose check yields the findings and records what it was asked."""
        asked: list = []

        def check_design(store, names):
            asked.append((store.root, names))
            return findings

        return SimpleNamespace(
            DesignStore=lambda root: SimpleNamespace(root=root), check_design=check_design, asked=asked,
        )

    def _issues(self, rule, design) -> list:
        with mock.patch.object(tooling_bridge, "load", return_value=design):
            return list(rule(SimpleNamespace(root=self.ROOT)))

    def test_each_finding_becomes_an_issue_with_its_path_line_and_message(self) -> None:
        finding = SimpleNamespace(path=Path("docs/design/A.md"), line=7, message="phase missing")
        issues = self._issues(tooling_bridge.design_rule("rule_x", False), self._design([finding]))
        self.assertEqual([(issue.path, issue.line, issue.message) for issue in issues],
                         [(Path("docs/design/A.md"), 7, "phase missing")])

    def test_only_the_named_rule_is_asked_for(self) -> None:
        design = self._design([])
        self._issues(tooling_bridge.design_rule("rule_x", False), design)
        self.assertEqual(design.asked, [(self.ROOT, ["rule_x"])])

    def test_the_rule_that_reports_a_missing_package_says_so_once(self) -> None:
        issues = self._issues(tooling_bridge.design_rule("rule_x", True), None)
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0].path, self.ROOT / "docs" / "design")

    def test_the_other_rules_say_nothing_when_the_package_is_missing(self) -> None:
        self.assertEqual(self._issues(tooling_bridge.design_rule("rule_x", False), None), [])

    def test_the_rule_documents_the_design_rule_it_runs(self) -> None:
        self.assertIn("rule_x", tooling_bridge.design_rule("rule_x", False).__doc__)


if __name__ == "__main__":
    unittest.main()
