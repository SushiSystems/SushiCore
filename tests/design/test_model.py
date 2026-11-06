# test_model.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
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


def test_parse_reads_the_title_and_the_open_status():
    """The title and the status line are read."""
    document = parse_topic(K_DOCUMENT)
    assert (document.title, document.is_open()) == ("Atmosphere", True)


def test_parse_reads_the_modules_line():
    """The Modules line gives the module paths without their code marks."""
    assert parse_topic(K_DOCUMENT).modules() == ["modules/atmosphere", "modules/clouds"]


def test_parse_leaves_a_heading_inside_a_fence_out_of_the_sections():
    """A heading inside a fenced block is not a section."""
    names = [name for _, name in parse_topic(K_DOCUMENT).sections]
    assert names == ["Problem", "Decision", "Design", "Phases", "Open questions"]


def test_parse_reads_the_phase_rows():
    """Each row of the phase table is a phase with its state."""
    assert [(p.ident, p.state) for p in parse_topic(K_DOCUMENT).phases] == [("A1", "built"), ("A2", "planned")]


def test_modules_none_is_an_empty_list():
    """`none` names no module."""
    assert parse_topic("# T\n\n**Status:** Open — x\n**Modules:** none\n").modules() == []


def test_a_missing_modules_line_is_none():
    """A topic with no Modules line is told apart from `none`."""
    assert parse_topic("# T\n\n**Status:** Open — x\n").modules() is None


def test_render_writes_the_five_sections():
    """A new topic carries the five sections and nothing else."""
    document = parse_topic(render_topic("Atmosphere", "The air.", ["modules/atmosphere"], []))
    assert [name for _, name in document.sections] == ["Problem", "Decision", "Design", "Phases", "Open questions"]


def test_render_writes_the_modules_line_and_the_empty_status():
    """A new topic names its modules and has no phase planned."""
    document = parse_topic(render_topic("Atmosphere", "The air.", ["modules/atmosphere"], []))
    assert (document.modules(), document.status) == (["modules/atmosphere"], "**Status:** Open — no phase planned yet")


def test_replace_phases_rewrites_the_table_and_keeps_the_generated_block():
    """Only the table changes; the generated block stays."""
    phases = [Phase("A1", "Scatter", "built"), Phase("A2", "Clouds", "built")]
    text = replace_phases(K_DOCUMENT, phases)
    assert ("| A2 | Clouds | built |" in text, "<!-- work:begin -->" in text, text.count("| Id | Phase | State |")) == (True, True, 1)


def test_replace_phases_keeps_the_prose():
    """The prose around the table is not lost."""
    text = replace_phases(K_DOCUMENT, [Phase("A1", "Scatter", "built")])
    assert "The sky is flat." in text and "## Open questions\n\nNone." in text


def test_replace_phases_fills_a_section_that_said_none():
    """`None.` gives way to the first table."""
    text = render_topic("T", "x", [], [])
    assert "| B1 | Start | planned |" in replace_phases(text, [Phase("B1", "Start", "planned")])


def test_replace_status_rewrites_the_status_line():
    """The status line is rewritten in place."""
    assert "**Status:** Shipped — 2026-10-28" in replace_status(K_DOCUMENT, "Shipped — 2026-10-28")


def test_replace_field_rewrites_a_metadata_line():
    """A metadata line is rewritten in place."""
    text = replace_field(K_DOCUMENT, "Modules", "`modules/atmosphere`")
    assert parse_topic(text).modules() == ["modules/atmosphere"]
