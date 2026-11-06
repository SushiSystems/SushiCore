# test_check.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the rules `design check` enforces."""

from __future__ import annotations

import pytest

from sushicore.design import check_design

pytestmark = pytest.mark.small


def _messages(store) -> list[str]:
    """Returns the message of every finding."""
    return [finding.message for finding in check_design(store)]


def _edit(store, name: str, old: str, new: str) -> None:
    """Replaces text in a topic's document."""
    path = store.topic(name).path
    store.files.write_text(path, store.files.read_text(path).replace(old, new))


def _atmosphere(store) -> None:
    """Opens the topic ATMOSPHERE on the module atmosphere with one phase."""
    store.create("ATMOSPHERE", modules=["modules/atmosphere"], about="The air.")
    store.add_phase("ATMOSPHERE", "A1", "Scatter light")


def test_a_module_two_topics_name_is_a_finding(memory_store):
    """The ownership rule: a module belongs to one topic."""
    memory_store.create("ATMOSPHERE", modules=["modules/atmosphere"], about="The air.")
    memory_store.create("CLOUDS", modules=["modules/clouds"], about="The clouds.")
    _edit(memory_store, "CLOUDS", "`modules/clouds`", "`modules/clouds`, `modules/atmosphere`")
    assert _messages(memory_store) == [
        "'modules/atmosphere' is owned by ATMOSPHERE; merge the topics with `design merge` or drop it here",
    ]


def test_a_missing_modules_line_is_a_finding(memory_store):
    """Every topic names its modules, or none."""
    memory_store.create("ATMOSPHERE", modules=["modules/atmosphere"], about="The air.")
    _edit(memory_store, "ATMOSPHERE", "**Modules:** `modules/atmosphere`\n", "")
    assert any("Modules:" in m for m in _messages(memory_store))


def test_a_module_that_is_not_in_the_repository_is_a_finding(memory_store):
    """Every module a topic names exists."""
    memory_store.create("ATMOSPHERE", modules=["modules/atmosphere"], about="The air.")
    _edit(memory_store, "ATMOSPHERE", "`modules/atmosphere`", "`modules/rain`")
    assert _messages(memory_store) == ["the module 'modules/rain' is not in the repository"]


def test_none_needs_an_about_line(memory_store):
    """A topic of no module says what it is."""
    memory_store.create("RELEASE", modules=[], about="The release.")
    _edit(memory_store, "RELEASE", "**About:** The release.\n", "")
    assert any("About:" in m for m in _messages(memory_store))


def test_a_section_that_is_not_one_of_the_five_is_a_finding(memory_store):
    """The five sections are the only ones."""
    _atmosphere(memory_store)
    _edit(memory_store, "ATMOSPHERE", "## Decision", "## Ruling")
    assert any("'## Ruling' is not one of the sections" in m for m in _messages(memory_store))


def test_an_unknown_phase_state_is_a_finding(memory_store):
    """A phase state is one of the four."""
    _atmosphere(memory_store)
    _edit(memory_store, "ATMOSPHERE", "| planned |", "| done |")
    assert any("a phase state is one of" in m for m in _messages(memory_store))


def test_a_commit_hash_is_a_finding(memory_store):
    """A commit hash belongs in the work folder's report."""
    _atmosphere(memory_store)
    _edit(memory_store, "ATMOSPHERE", "## Problem\n\nNone.", "## Problem\n\nFixed in 1a2b3c4d.")
    assert any("commit hash" in m for m in _messages(memory_store))


def test_a_dated_record_of_work_is_a_finding(memory_store):
    """When work was done belongs in the work folder's report."""
    _atmosphere(memory_store)
    _edit(memory_store, "ATMOSPHERE", "## Problem\n\nNone.", "## Problem\n\nMerged on 2026-10-01.")
    assert any("when work was done" in m for m in _messages(memory_store))


def test_a_loose_document_is_a_finding(memory_store):
    """A topic is a folder."""
    memory_store.files.write_text(memory_store.design / "LOOSE.md", "# Loose\n\n**Status:** Open — x\n")
    assert any("a topic is a folder" in m for m in _messages(memory_store))


def test_a_work_folder_naming_no_phase_or_topic_is_a_finding(memory_store):
    """Implements names a topic's phase."""
    _atmosphere(memory_store)
    work = memory_store.root / "docs" / "agent" / "2026_10_28_WORK" / "SPEC.md"
    memory_store.files.write_text(work, "# Work\n\n**Status:** Open — x\n**Implements:** ATMOSPHERE#A9, RAIN#R1\n")
    assert _messages(memory_store) == ["'ATMOSPHERE' has no phase 'A9'", "'RAIN' is not a design topic"]
