# test_toolkit_choice_file.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The recorded choice round-trips, and an unusable file reads as absent."""

from __future__ import annotations

import pytest

from sushicore.provision.gpu.toolkit_choice import ToolkitChoice
from sushicore.provision.gpu.toolkit_choice_file import ToolkitChoiceFile


pytestmark = pytest.mark.medium


def test_a_written_choice_reads_back(tmp_path):
    """Check that write then read returns the same choice."""
    choices = ToolkitChoiceFile(tmp_path / "cuda" / "choice.json")
    choice = ToolkitChoice("sm=89;driver=13.1", "windows-x86_64", "13.1.2")

    choices.write(choice)

    assert choices.read() == choice


def _file_holding(tmp_path, text: str | None) -> ToolkitChoiceFile:
    """Return the choice file at a path under *tmp_path*, holding *text* or absent when None."""
    path = tmp_path / "choice.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(text or "", encoding="utf-8")
    if text is None:
        path.unlink()
    return ToolkitChoiceFile(path)


@pytest.mark.parametrize("text", [None, '{"format": 2, "release": "13.1.2"}', "{"],
                         ids=["missing", "another-format", "corrupt"])
def test_an_unusable_file_reads_as_none(tmp_path, text):
    """Check that a missing file, a file of a future layout and one that does not parse read as no choice."""
    assert _file_holding(tmp_path, text).read() is None
