# test_check.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the rules `backlog check` enforces."""

from __future__ import annotations

import datetime
from pathlib import Path

import pytest

from sushicore.backlog import BacklogStore, WorkEntry, check_backlog
from sushicore.backlog.check import (
    BacklogCheck,
    rule_blocked_ready,
    rule_design_coverage,
    rule_ids,
    rule_pins,
    rule_references,
    rule_sorted,
)
from sushicore.backlog.store import AreaFile, BacklogConfig, IdLedger, Located

K_DAY = datetime.date(2026, 10, 28)
K_ROOT = Path("repo")
K_AREA_FILE = K_ROOT / "docs" / "backlog" / "PHYSICS.md"
K_TOPIC = K_ROOT / "docs" / "design" / "PHYSICS" / "README.md"


def _messages(store: BacklogStore, open_designs=lambda: ()) -> list[str]:
    """Returns the message of every fault."""
    return [fault.message for fault in check_backlog(store, open_designs)]


def _work(editor, **changes):
    """Adds a work entry with default values."""
    values = dict(area="PHYSICS", priority="P2", title="Fix the step", done_when="it passes")
    values.update(changes)
    return editor.add_work(**values)


def _entry(
    ident: str = "RW-1", state: str = "open", blocked_by: str = "", source: str = "",
) -> WorkEntry:
    """Returns a work entry with default values."""
    return WorkEntry(ident, "P2", state, "Fix the step", "it passes", blocked_by, source, K_DAY)


def _located(*entries: WorkEntry) -> list[Located]:
    """Returns each entry as read from the PHYSICS file."""
    return [Located(entry, K_AREA_FILE, 1, "PHYSICS") for entry in entries]


def _faults(rule, store: BacklogStore, **values) -> list[str]:
    """Returns the messages a rule yields on a check built from values, with no file read."""
    return [fault.message for fault in rule(BacklogCheck(store, **values))]


def _pins(count: int) -> tuple[str, ...]:
    """Returns `count` pins, RW-1 onward."""
    return tuple(f"RW-{number}" for number in range(1, count + 1))


@pytest.mark.medium
def test_a_store_after_add_work_and_add_issue_is_clean(editor, store):
    """A store built by `add work` and `add issue` checks clean."""
    _work(editor)
    editor.add_issue(area="BUILD", origin="toolchain", symptom="The link fails", workaround="none")
    assert _messages(store) == []


@pytest.mark.medium
def test_a_repository_without_a_store_is_clean_unless_it_holds_the_retired_files(tmp_path: Path):
    """The retired files send a repository to `import`."""
    assert check_backlog(BacklogStore(tmp_path)) == []
    retired = tmp_path / "docs" / "design" / "REMAINING_WORK.md"
    retired.parent.mkdir(parents=True)
    retired.write_text("# Remaining work\n", encoding="utf-8")
    assert "backlog import" in _messages(BacklogStore(tmp_path))[0]


@pytest.mark.medium
def test_a_hand_edit_that_changes_the_shape_is_a_fault(editor, store):
    """A file the tool would not write fails."""
    _work(editor)
    path = store.area_path("PHYSICS")
    path.write_text(path.read_text(encoding="utf-8").replace("| RW-1 |", "|RW-1|"), encoding="utf-8")
    assert any("shape the tool writes" in message for message in _messages(store))


@pytest.mark.small
def test_a_duplicate_id_is_a_fault(memory_store):
    """Two branches that took one number are sent to `renumber`."""
    found = _faults(
        rule_ids, memory_store, ledger=IdLedger(next={"RW": 3, "KI": 1}),
        located=_located(_entry("RW-1"), _entry("RW-1")),
    )
    assert found == ["RW-1: the ID is used twice; run `backlog renumber`"]


@pytest.mark.small
def test_an_id_at_or_past_the_counter_is_a_fault(memory_store):
    """An entry numbered past `ids.toml` was written by a branch that never took the number."""
    found = _faults(
        rule_ids, memory_store, ledger=IdLedger(next={"RW": 2, "KI": 1}),
        located=_located(_entry("RW-7")),
    )
    assert found == ["RW-7: at or past the counter in ids.toml; run `backlog renumber`"]


@pytest.mark.small
def test_an_id_that_was_closed_is_a_fault(memory_store):
    """A closed number is never reused."""
    found = _faults(
        rule_ids, memory_store,
        ledger=IdLedger(next={"RW": 5, "KI": 1}, closed={"RW": {2}, "KI": set()}),
        located=_located(_entry("RW-2")),
    )
    assert found == ["RW-2: the ID was closed and is never reused"]


@pytest.mark.medium
def test_a_source_path_that_does_not_exist_is_a_fault(editor, store):
    """A Source names a path that exists from the repository root."""
    _work(editor, source="docs/design/README.md")
    assert any("does not exist" in message for message in _messages(store))


@pytest.mark.medium
def test_a_source_path_that_exists_is_clean(editor, store):
    """A Source naming a file of the repository raises no fault."""
    _work(editor, source="docs/design/README.md")
    (store.root / "docs" / "design" / "README.md").write_text("# Design\n", encoding="utf-8")
    assert _messages(store) == []


@pytest.mark.small
def test_a_reference_to_no_open_entry_is_a_fault(memory_store):
    """A cited ID names an entry that is still open."""
    found = _faults(
        rule_references, memory_store,
        located=_located(_entry("RW-2", state="blocked", blocked_by="RW-9")),
    )
    assert found == ["RW-2: 'RW-9' names no open entry"]


@pytest.mark.small
def test_a_blocked_entry_whose_blocks_closed_must_be_opened(memory_store):
    """A block on a closed entry is stale."""
    found = _faults(
        rule_blocked_ready, memory_store,
        located=_located(_entry("RW-2", state="blocked", blocked_by="RW-1")),
    )
    assert found == ["RW-2: every block is closed; set State to open"]


@pytest.mark.small
def test_a_pin_on_a_closed_entry_is_a_fault(memory_store):
    """Pins name open work."""
    found = _faults(rule_pins, memory_store, config=BacklogConfig(("PHYSICS",), ("RW-9",)))
    assert found == ["the pin RW-9 names no open work entry"]


@pytest.mark.small
def test_a_pin_on_a_decision_is_a_fault(memory_store):
    """The owner takes a decision, so it is never pinned."""
    found = _faults(
        rule_pins, memory_store, config=BacklogConfig(("PHYSICS",), ("RW-1",)),
        located=_located(_entry("RW-1", state="decision")),
    )
    assert found == ["the pin RW-1 is a decision; the owner takes it, not an agent"]


@pytest.mark.small
def test_more_pins_than_the_ceiling_is_a_fault(memory_store):
    """Ten pins are the most the owner keeps."""
    found = _faults(
        rule_pins, memory_store, config=BacklogConfig(("PHYSICS",), _pins(11)),
        located=_located(*(_entry(pin) for pin in _pins(11))),
    )
    assert found == ["11 pins; the ceiling is 10"]


@pytest.mark.small
def test_the_rows_of_a_table_out_of_id_order_are_a_fault(memory_store):
    """Rows are sorted by ID."""
    area = AreaFile("PHYSICS", work=[_entry("RW-2"), _entry("RW-1")])
    assert _faults(rule_sorted, memory_store, areas=[area]) == ["the rows of a table are sorted by ID"]


@pytest.mark.medium
def test_a_stale_index_is_a_fault(editor, store):
    """The index is regenerated by every command."""
    _work(editor)
    (store.folder / "README.md").write_text("# Backlog\n", encoding="utf-8")
    assert any("stale" in message for message in _messages(store))


@pytest.mark.medium
def test_a_detail_whose_entry_is_closed_is_a_fault(editor, store):
    """A detail belongs to an open entry."""
    store.write_detail("RW-5", "# RW-5\n")
    assert any("RW-5 is closed" in message for message in _messages(store))


@pytest.mark.small
def test_an_open_design_no_entry_cites_is_a_fault(memory_store):
    """Each open design is reached by work."""
    found = _faults(rule_design_coverage, memory_store, open_designs=lambda: [K_TOPIC])
    assert found == ["an open design topic is cited by the Source of a work entry"]


@pytest.mark.small
def test_an_open_design_a_source_cites_is_clean(memory_store):
    """A work entry whose Source is the topic reaches it."""
    cited = _entry(source="`docs/design/PHYSICS/README.md`")
    found = _faults(
        rule_design_coverage, memory_store, open_designs=lambda: [K_TOPIC], located=_located(cited),
    )
    assert found == []


@pytest.mark.medium
def test_a_file_the_store_does_not_know_is_a_fault(editor, store):
    """Only the configured areas live in docs/backlog."""
    (store.folder / "NOTES.md").write_text("# Notes\n", encoding="utf-8")
    assert any("not a file of the store" in message for message in _messages(store))
