# test_toolkit_choice_file.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The recorded choice round-trips, and an unusable file reads as absent."""

from __future__ import annotations

from sushicore.provision.gpu.toolkit_choice import ToolkitChoice
from sushicore.provision.gpu.toolkit_choice_file import ToolkitChoiceFile


def test_a_written_choice_reads_back(tmp_path):
    """Check that write then read returns the same choice."""
    choices = ToolkitChoiceFile(tmp_path / "cuda" / "choice.json")
    choice = ToolkitChoice("sm=89;driver=13.1", "windows-x86_64", "13.1.2")

    choices.write(choice)

    assert choices.read() == choice


def test_a_missing_file_reads_as_none(tmp_path):
    """Check that no file means no choice."""
    assert ToolkitChoiceFile(tmp_path / "choice.json").read() is None


def test_another_format_reads_as_none(tmp_path):
    """Check that a file of a future layout is ignored."""
    path = tmp_path / "choice.json"
    path.write_text('{"format": 2, "release": "13.1.2"}', encoding="utf-8")

    assert ToolkitChoiceFile(path).read() is None


def test_a_corrupt_file_reads_as_none(tmp_path):
    """Check that a file that does not parse is ignored."""
    path = tmp_path / "choice.json"
    path.write_text("{", encoding="utf-8")

    assert ToolkitChoiceFile(path).read() is None
