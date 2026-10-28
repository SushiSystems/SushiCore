# test_model.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests the frame of a topic: reading it, writing a new one and replacing its parts."""

from __future__ import annotations

import pytest

from sushicore.design.model import (
    Phase,
    parse_topic,
    render_topic,
    replace_field,
    replace_phases,
    replace_status,
)

pytestmark = pytest.mark.small

K_DOCUMENT = """# Atmosphere

**Status:** Open — phase A2 to be built
**About:** The air.
**Modules:** `modules/atmosphere`, `modules/clouds`

## Problem

The sky is flat.

## Decision

None.

## Design

```
## Not a section
```

## Phases

| Id | Phase | State |
| --- | --- | --- |
| A1 | Scatter | built |
| A2 | Clouds | planned |

<!-- work:begin -->
<!-- work:end -->

## Open questions

None.
"""


def test_parse_reads_the_status_the_metadata_the_sections_and_the_phases():
    """The frame is read; a heading inside a fence is not a section."""
    document = parse_topic(K_DOCUMENT)
    assert document.title == "Atmosphere"
    assert document.is_open()
    assert document.modules() == ["modules/atmosphere", "modules/clouds"]
    assert [name for _, name in document.sections] == ["Problem", "Decision", "Design", "Phases", "Open questions"]
    assert [(p.ident, p.state) for p in document.phases] == [("A1", "built"), ("A2", "planned")]


def test_modules_none_is_an_empty_list_and_a_missing_line_is_none():
    """`none` and a missing line are told apart."""
    assert parse_topic("# T\n\n**Status:** Open — x\n**Modules:** none\n").modules() == []
    assert parse_topic("# T\n\n**Status:** Open — x\n").modules() is None


def test_render_writes_the_five_sections_and_the_modules():
    """A new topic carries its frame and nothing else."""
    text = render_topic("Atmosphere", "The air.", ["modules/atmosphere"], [])
    document = parse_topic(text)
    assert document.modules() == ["modules/atmosphere"]
    assert len(document.sections) == 5
    assert document.status == "**Status:** Open — no phase planned yet"


def test_replace_phases_keeps_the_generated_block_and_the_prose():
    """Only the table changes."""
    phases = [Phase("A1", "Scatter", "built"), Phase("A2", "Clouds", "built")]
    text = replace_phases(K_DOCUMENT, phases)
    assert "| A2 | Clouds | built |" in text
    assert "<!-- work:begin -->" in text
    assert text.count("| Id | Phase | State |") == 1


def test_replace_phases_fills_a_section_that_said_none():
    """`None.` gives way to the first table."""
    text = render_topic("T", "x", [], [])
    assert "| B1 | Start | planned |" in replace_phases(text, [Phase("B1", "Start", "planned")])


def test_replace_status_and_field():
    """The status line and a metadata line are rewritten in place."""
    text = replace_status(K_DOCUMENT, "Shipped — 2026-10-28")
    assert "**Status:** Shipped — 2026-10-28" in text
    text = replace_field(text, "Modules", "`modules/atmosphere`")
    assert parse_topic(text).modules() == ["modules/atmosphere"]
