# test_store.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests the store: area files, the counters, the configuration and the index."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.backlog import BacklogError, BacklogStore
from sushicore.backlog.store import format_ranges, parse_area, parse_ranges, render_area

pytestmark = pytest.mark.medium


def test_an_area_file_round_trips_through_the_shape_the_tool_writes(editor, store):
    """What the tool writes it reads back unchanged."""
    editor.add_work(area="PHYSICS", priority="P1", title="Fix the step", done_when="it passes")
    editor.add_issue(area="PHYSICS", origin="toolchain", symptom="The link fails", workaround="none")
    path = store.area_path("PHYSICS")
    text = path.read_text(encoding="utf-8")
    parsed, faults = parse_area(path, text)
    assert faults == []
    assert render_area(parsed) == text
    assert [entry.ident for entry in parsed.entries()] == ["RW-1", "KI-1"]


def test_a_row_out_of_shape_is_a_fault_and_the_store_refuses_to_read_it(editor, store):
    """A hand-edited row stops every command until it is put back."""
    path = store.area_path("PHYSICS")
    path.write_text(path.read_text(encoding="utf-8") + "| RW-9 | P1 |\n", encoding="utf-8")
    _, faults = parse_area(path, path.read_text(encoding="utf-8"))
    assert faults
    with pytest.raises(BacklogError):
        store.read_area("PHYSICS")


def test_merge_conflict_markers_are_dropped_when_tolerated(editor, store):
    """Renumber reads both sides of a conflict."""
    editor.add_work(area="PHYSICS", priority="P1", title="Fix the step", done_when="it passes")
    path = store.area_path("PHYSICS")
    lines = path.read_text(encoding="utf-8").splitlines()
    row = next(line for line in lines if line.startswith("| RW-1 "))
    other = row.replace("Fix the step", "Fix the join")
    conflicted = "\n".join(
        [*lines[: lines.index(row)], "<<<<<<< HEAD", row, "=======", other, ">>>>>>> side", *lines[lines.index(row) + 1:]])
    parsed, faults = parse_area(path, conflicted, tolerate_conflicts=True)
    assert faults == []
    assert [entry.title for entry in parsed.work] == ["Fix the step", "Fix the join"]


def test_ledger_takes_numbers_in_order_and_remembers_closed_ones(store):
    """IDs are never reused once closed."""
    ledger = store.ledger()
    assert ledger.take("RW") == "RW-1"
    ledger.close("RW-1")
    store.write_ledger(ledger)
    again = store.ledger()
    assert again.take("RW") == "RW-2"
    assert again.is_closed("RW-1")


def test_ranges_compress_and_expand():
    """The closed IDs are written as ranges."""
    assert format_ranges({1, 2, 3, 7, 9, 10}) == "1-3,7,9-10"
    assert parse_ranges("1-3,7,9-10") == {1, 2, 3, 7, 9, 10}


def test_config_without_areas_is_an_error(tmp_path: Path):
    """A store names its areas."""
    folder = tmp_path / "docs" / "backlog"
    folder.mkdir(parents=True)
    (folder / "backlog.toml").write_text("[backlog]\nareas = []\n", encoding="utf-8")
    with pytest.raises(BacklogError):
        BacklogStore(tmp_path).config()


def test_index_counts_each_area(editor, store):
    """The generated README counts entries by state and priority."""
    editor.add_work(area="BUILD", priority="P0", title="Fix the gate", done_when="the gate passes")
    index = (store.folder / "README.md").read_text(encoding="utf-8")
    assert "| [Build](BUILD.md) | 1 | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 0 | 0 |" in index
    assert index == store.render_index()


def test_find_names_the_area_and_raises_for_an_unknown_id(editor, store):
    """`find` locates an entry, or says it is not open."""
    editor.add_work(area="BUILD", priority="P2", title="Fix the gate", done_when="the gate passes")
    assert store.find("RW-1").area == "BUILD"
    with pytest.raises(BacklogError):
        store.find("RW-2")
