# test_store.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the store: area files, the counters, the configuration and the index."""

from __future__ import annotations

import datetime
from pathlib import Path

import pytest

from sushicore.backlog import BacklogEditor, BacklogError, BacklogStore
from sushicore.backlog.errors import EntryNotFoundError
from sushicore.backlog.store import (
    AreaFile,
    IdLedger,
    format_ranges,
    parse_area,
    parse_ranges,
    render_area,
)
from sushicore.files_memory import MemoryFiles

pytestmark = pytest.mark.small

K_AREA_PATH = Path("PHYSICS.md")


def _rows_out_of_shape() -> str:
    """Returns an area file with a row that has two cells."""
    return render_area(AreaFile("PHYSICS")) + "| RW-9 | P1 |\n"


def test_an_area_file_round_trips_through_the_shape_the_tool_writes(memory_editor, memory_store):
    """What the tool writes it reads back unchanged."""
    memory_editor.add_work(area="PHYSICS", priority="P1", title="Fix the step", done_when="it passes")
    memory_editor.add_issue(
        area="PHYSICS", origin="toolchain", symptom="The link fails", workaround="none")
    path = memory_store.area_path("PHYSICS")
    text = memory_store.files.read_text(path)
    parsed, faults = parse_area(path, text)
    assert faults == []
    assert render_area(parsed) == text
    assert [entry.ident for entry in parsed.entries()] == ["RW-1", "KI-1"]


def test_a_row_out_of_shape_is_a_fault():
    """A row of two cells is reported with its line."""
    _, faults = parse_area(K_AREA_PATH, _rows_out_of_shape())
    assert [fault.line for fault in faults] == [len(render_area(AreaFile("PHYSICS")).splitlines()) + 1]


def test_the_store_refuses_to_read_a_row_out_of_shape(memory_store):
    """A hand-edited row stops every command until it is put back."""
    memory_store.files.write_text(memory_store.area_path("PHYSICS"), _rows_out_of_shape())
    with pytest.raises(BacklogError):
        memory_store.read_area("PHYSICS")


def test_an_area_file_with_another_title_is_a_fault():
    """The first line is the title the tool writes."""
    text = render_area(AreaFile("PHYSICS")).replace("# Physics", "# Matter", 1)
    _, faults = parse_area(K_AREA_PATH, text)
    assert [fault.line for fault in faults] == [1]


def test_an_area_file_with_other_columns_is_a_fault():
    """The header of each table holds the columns of its kind."""
    text = render_area(AreaFile("PHYSICS")).replace(" Pri ", " Prio ", 1)
    _, faults = parse_area(K_AREA_PATH, text)
    assert [fault.line for fault in faults] == [5]


def test_merge_conflict_markers_are_dropped_when_tolerated(memory_editor, memory_store):
    """Renumber reads both sides of a conflict."""
    memory_editor.add_work(area="PHYSICS", priority="P1", title="Fix the step", done_when="it passes")
    path = memory_store.area_path("PHYSICS")
    lines = memory_store.files.read_text(path).splitlines()
    row = next(line for line in lines if line.startswith("| RW-1 "))
    other = row.replace("Fix the step", "Fix the join")
    conflicted = "\n".join(
        [*lines[: lines.index(row)], "<<<<<<< HEAD", row, "=======", other, ">>>>>>> side",
         *lines[lines.index(row) + 1:]])
    parsed, faults = parse_area(path, conflicted, tolerate_conflicts=True)
    assert faults == []
    assert [entry.title for entry in parsed.work] == ["Fix the step", "Fix the join"]


def test_ledger_takes_numbers_in_order():
    """Each kind counts from 1 and moves on at every take."""
    ledger = IdLedger()
    assert [ledger.take("RW"), ledger.take("RW"), ledger.take("KI")] == ["RW-1", "RW-2", "KI-1"]


def test_ledger_remembers_a_closed_number():
    """A closed number is reported closed and an open one is not."""
    ledger = IdLedger()
    ledger.close("RW-1")
    assert (ledger.is_closed("RW-1"), ledger.is_closed("RW-2")) == (True, False)


def test_ledger_round_trips_through_ids_toml(memory_store):
    """IDs are never reused once closed, after the ledger is written and read back."""
    ledger = memory_store.ledger()
    ledger.take("RW")
    ledger.close("RW-1")
    memory_store.write_ledger(ledger)
    again = memory_store.ledger()
    assert (again.take("RW"), again.is_closed("RW-1")) == ("RW-2", True)


def test_ranges_compress():
    """The closed IDs are written as ranges."""
    assert format_ranges({1, 2, 3, 7, 9, 10}) == "1-3,7,9-10"


def test_ranges_expand():
    """A list of ranges names every number in it."""
    assert parse_ranges("1-3,7,9-10") == {1, 2, 3, 7, 9, 10}


def test_config_without_areas_is_an_error():
    """A store names its areas."""
    path = Path("repo") / "docs" / "backlog" / "backlog.toml"
    store = BacklogStore(Path("repo"), files=MemoryFiles({path: "[backlog]\nareas = []\n"}))
    with pytest.raises(BacklogError):
        store.config()


def test_index_counts_each_area(memory_editor, memory_store):
    """The generated README counts entries by state and priority."""
    memory_editor.add_work(area="BUILD", priority="P0", title="Fix the gate", done_when="the gate passes")
    index = memory_store.files.read_text(memory_store.folder / "README.md")
    assert "| [Build](BUILD.md) | 1 | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 0 | 0 |" in index


def test_find_names_the_area(memory_editor, memory_store):
    """`find` locates an entry."""
    memory_editor.add_work(area="BUILD", priority="P2", title="Fix the gate", done_when="the gate passes")
    assert memory_store.find("RW-1").area == "BUILD"


def test_find_raises_for_an_unknown_id(memory_store):
    """`find` says an ID is not open."""
    with pytest.raises(EntryNotFoundError):
        memory_store.find("RW-2")


def test_an_entry_is_added_and_found_with_no_disk():
    """The store keeps its promise on the in-memory files: config, ledger, area and index."""
    files = MemoryFiles()
    store = BacklogStore(Path("repo"), lambda: datetime.date(2026, 10, 28), files)
    editor = BacklogEditor(store)
    editor.add_area("PHYSICS")
    editor.add_work(area="PHYSICS", priority="P1", title="Fix the step", done_when="it passes")
    [entry] = store.entries()
    assert store.find(entry.ident).area == "PHYSICS"
    assert files.is_file(store.area_path("PHYSICS"))
    assert "PHYSICS" in store.render_index()
