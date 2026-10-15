# test_check_package_layers.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests the rules of tools/layering/check_package_layers.py on packages built on disk."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from layering.check_package_layers import (  # noqa: E402
    Repository,
    rule_forbidden_import,
    rule_ui_component,
    rule_unlayered_module,
    rule_upward_import,
)

K_COMPONENT = """from dataclasses import dataclass
from typing import final

from rich.text import Text

from ..theme import Theme


@final
@dataclass(frozen=True, slots=True)
class Title:
    text: str

    def render(self, theme: Theme) -> Text:
        return Text(self.text)
"""


class PackageLayersTest(unittest.TestCase):
    """Builds a repository with source/sushicore/ for each test."""

    def setUp(self) -> None:
        self._folder = tempfile.TemporaryDirectory()
        self.repository = Repository(Path(self._folder.name))

    def tearDown(self) -> None:
        self._folder.cleanup()

    def write(self, relative: str, text: str = "") -> None:
        """Writes a file below source/sushicore/."""
        path = self.repository.root / "source" / "sushicore" / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def messages(self, rule) -> list[str]:
        """Returns the message of each issue a rule yields."""
        return [issue.message for issue in rule(self.repository)]

    def test_reports_a_module_without_a_layer(self) -> None:
        self.write("provision/home.py")
        self.write("provision/brand_new.py")
        self.assertEqual(self.messages(rule_unlayered_module),
                         ["brand_new has no layer in the sushicore.provision table"])

    def test_reports_every_form_of_an_upward_import(self) -> None:
        self.write("provision/home.py", "from . import steps\nfrom sushicore.provision import commands\n")
        self.write("provision/gpu/cuda.py", "def later():\n    from .. import steps\n")
        self.assertEqual(sorted(self.messages(rule_upward_import)), [
            "gpu.cuda imports steps, which is not in a lower layer",
            "home imports commands, which is not in a lower layer",
            "home imports steps, which is not in a lower layer",
        ])

    def test_a_sideways_import_passes_only_where_the_package_allows_it(self) -> None:
        self.write("provision/config.py", "from . import home\n")
        self.write("docs_bundle/page_text.py", "from .publish_list import read\n")
        self.assertEqual(self.messages(rule_upward_import),
                         ["page_text imports publish_list, which is not in a lower layer"])

    def test_reports_a_forbidden_import_at_module_level_only_where_asked(self) -> None:
        self.write("docs_bundle/commands.py", "import typer\n\ndef run():\n    import click\n")
        self.write("provision/steps.py", "def run():\n    import sushihub.cli\n")
        self.assertEqual(sorted(self.messages(rule_forbidden_import)), [
            "sushicore.docs_bundle may not import typer",
            "sushicore.provision may not import sushihub.cli",
        ])

    def test_accepts_a_component_of_the_right_shape(self) -> None:
        self.write("ui/title.py", K_COMPONENT)
        self.assertEqual(self.messages(rule_ui_component), [])

    def test_reports_each_way_a_component_breaks_its_shape(self) -> None:
        broken = (K_COMPONENT.replace("@final\n", "").replace("slots=True", "slots=False")
                  .replace("self, theme: Theme", "self, theme: Theme, width: int")
                  .replace("from ..theme import Theme", "from ..theme import Theme\nfrom ..console import Console"))
        self.write("ui/title.py", broken)
        self.assertEqual(self.messages(rule_ui_component), [
            "Title is not marked final",
            "Title is not a frozen dataclass with slots",
            "Title.render does not take exactly self and theme",
            "a component may not import sushicore.console",
        ])

    def test_reports_a_file_whose_class_is_not_named_after_it(self) -> None:
        self.write("ui/header.py", K_COMPONENT)
        self.assertEqual(self.messages(rule_ui_component),
                         ["defines ['Title'], not the one public class Header"])


if __name__ == "__main__":
    unittest.main()
