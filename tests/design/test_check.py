# test_check.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests the rules `design check` enforces."""

from __future__ import annotations

import pytest

from sushicore.design import check_design

pytestmark = pytest.mark.medium


def _messages(store) -> list[str]:
    """Returns the message of every finding."""
    return [finding.message for finding in check_design(store)]


def _edit(store, name: str, old: str, new: str) -> None:
    """Replaces text in a topic's document."""
    path = store.topic(name).path
    path.write_text(path.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")


def test_a_topic_the_tool_wrote_is_clean(store):
    """`design new` writes a topic that passes."""
    store.create("ATMOSPHERE", modules=["modules/atmosphere"], about="The air.")
    store.add_phase("ATMOSPHERE", "A1", "Scatter light")
    assert _messages(store) == []


def test_a_module_two_topics_name_is_a_finding(store):
    """The ownership rule: a module belongs to one topic."""
    store.create("ATMOSPHERE", modules=["modules/atmosphere"], about="The air.")
    store.create("CLOUDS", modules=["modules/clouds"], about="The clouds.")
    _edit(store, "CLOUDS", "`modules/clouds`", "`modules/clouds`, `modules/atmosphere`")
    found = _messages(store)
    assert found == ["'modules/atmosphere' is owned by ATMOSPHERE; merge the topics with `design merge` or drop it here"]


def test_a_missing_modules_line_and_a_missing_module_are_findings(store):
    """Every topic names its modules, and they exist."""
    store.create("ATMOSPHERE", modules=["modules/atmosphere"], about="The air.")
    _edit(store, "ATMOSPHERE", "`modules/atmosphere`", "`modules/rain`")
    assert any("'modules/rain' is not in the repository" in m for m in _messages(store))
    _edit(store, "ATMOSPHERE", "**Modules:** `modules/rain`\n", "")
    assert any("Modules:" in m for m in _messages(store))


def test_none_needs_an_about_line(store):
    """A topic of no module says what it is."""
    store.create("RELEASE", modules=[], about="The release.")
    assert _messages(store) == []
    _edit(store, "RELEASE", "**About:** The release.\n", "")
    assert any("About:" in m for m in _messages(store))


def test_sections_phases_hashes_and_dated_work_are_findings(store):
    """The format rules of a design document."""
    store.create("ATMOSPHERE", modules=["modules/atmosphere"], about="The air.")
    store.add_phase("ATMOSPHERE", "A1", "Scatter light")
    _edit(store, "ATMOSPHERE", "## Decision", "## Ruling")
    _edit(store, "ATMOSPHERE", "| planned |", "| done |")
    _edit(store, "ATMOSPHERE", "## Problem\n\nNone.", "## Problem\n\nFixed in 1a2b3c4d. Merged on 2026-10-01.")
    found = _messages(store)
    assert any("'## Ruling' is not one of the sections" in m for m in found)
    assert any("a phase state is one of" in m for m in found)
    assert any("commit hash" in m for m in found)
    assert any("when work was done" in m for m in found)


def test_a_loose_document_and_a_work_folder_naming_no_phase_are_findings(store):
    """A topic is a folder; Implements names a topic's phase."""
    store.create("ATMOSPHERE", modules=["modules/atmosphere"], about="The air.")
    (store.design / "LOOSE.md").write_text("# Loose\n\n**Status:** Open — x\n", encoding="utf-8")
    work = store.root / "docs" / "agent" / "2026_10_28_WORK" / "SPEC.md"
    work.parent.mkdir(parents=True)
    work.write_text("# Work\n\n**Status:** Open — x\n**Implements:** ATMOSPHERE#A9, RAIN#R1\n", encoding="utf-8")
    found = _messages(store)
    assert any("a topic is a folder" in m for m in found)
    assert "'ATMOSPHERE' has no phase 'A9'" in found
    assert "'RAIN' is not a design topic" in found
