# test_plain_text.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests the removal of Rich markup tags from text."""

import pytest

from sushicore.plain_text import plain_text


pytestmark = pytest.mark.small


def test_tags_are_removed_and_their_text_kept():
    assert plain_text("[success]ok[/success] and [bold]more[/]") == "ok and more"


def test_a_bracket_that_is_no_tag_is_kept():
    assert plain_text("found [1, 2] in path") == "found [1, 2] in path"


def test_text_with_a_mismatched_closing_tag_comes_back_as_it_was():
    assert plain_text("[bold]one[/italic]") == "[bold]one[/italic]"


def test_plain_text_is_unchanged():
    assert plain_text("nothing to strip") == "nothing to strip"


def test_importing_the_module_does_not_load_rich():
    import subprocess
    import sys

    code = "import sys, sushicore.plain_text; sys.exit(1 if 'rich' in sys.modules else 0)"
    assert subprocess.run([sys.executable, "-c", code], env={"PYTHONPATH": "source"}).returncode == 0
