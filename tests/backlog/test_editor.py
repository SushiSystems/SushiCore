# test_editor.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the changes the backlog commands make: add, promote, set, move, close, pins and areas."""

from __future__ import annotations

import pytest

from sushicore.backlog import RefusedChangeError
from sushicore.backlog.errors import EntryNotFoundError
from sushicore.backlog.store import K_PIN_CEILING


def _work(editor, area: str = "PHYSICS", **changes):
    """Adds a work entry with default values."""
    values = dict(area=area, priority="P2", title="Fix the step", done_when="it passes")
    values.update(changes)
    return editor.add_work(**values)


def _pinned(editor, count: int) -> None:
    """Adds `count` work entries and pins each, in order."""
    for _ in range(count):
        editor.pin(_work(editor).ident)


@pytest.mark.small
def test_add_takes_the_next_id_of_its_kind(memory_editor):
    """IDs are counted per kind."""
    first = _work(memory_editor)
    issue = memory_editor.add_issue(
        area="BUILD", origin="toolchain", symptom="The link fails", workaround="none")
    second = _work(memory_editor)
    assert (first.ident, issue.ident, second.ident) == ("RW-1", "KI-1", "RW-2")


@pytest.mark.small
def test_add_with_blocked_by_makes_the_entry_blocked(memory_editor):
    """A block given at add sets the state."""
    _work(memory_editor)
    blocked = _work(memory_editor, blocked_by="RW-1")
    assert blocked.state == "blocked"


@pytest.mark.parametrize(
    "changes", [{"title": "x" * 91}, {"area": "AUDIO"}], ids=["a broken title", "an unknown area"],
)
@pytest.mark.small
def test_add_refuses_what_is_wrong_without_writing_or_taking_a_number(memory_editor, changes):
    """A refused add writes nothing and takes no number."""
    with pytest.raises(RefusedChangeError):
        _work(memory_editor, **changes)
    assert _work(memory_editor).ident == "RW-1"


@pytest.mark.small
def test_add_puts_a_bare_source_in_backticks(memory_editor):
    """A path given bare is written as the Source cell writes it."""
    entry = _work(memory_editor, source="docs/design/PHYSICS §3")
    assert entry.source == "`docs/design/PHYSICS` §3"


@pytest.mark.small
def test_promote_writes_the_new_work_into_the_issue_fix(memory_editor, memory_store):
    """Promoting an issue opens its work entry and points the issue at it."""
    memory_editor.add_issue(
        area="BUILD", origin="own", symptom="The link fails", workaround="link twice",
        fix="none, not yet")
    work = memory_editor.promote("KI-1", priority="P1", title="Fix the link", done_when="one link passes")
    assert (work.ident, memory_store.find("KI-1").entry.fix) == ("RW-1", "RW-1")


@pytest.mark.small
def test_promote_opens_the_work_in_the_area_of_the_issue(memory_editor, memory_store):
    """The new work entry sits beside the issue."""
    memory_editor.add_issue(
        area="BUILD", origin="own", symptom="The link fails", workaround="link twice",
        fix="none, not yet")
    memory_editor.promote("KI-1", priority="P1", title="Fix the link", done_when="one link passes")
    assert memory_store.find("RW-1").area == "BUILD"


@pytest.mark.small
def test_set_changes_one_column(memory_editor, memory_store):
    """`set` rewrites one cell."""
    _work(memory_editor)
    memory_editor.set_value("RW-1", "Pri", "P0")
    assert memory_store.find("RW-1").entry.priority == "P0"


@pytest.mark.small
def test_set_refuses_a_broken_value(memory_editor):
    """`set` keeps the rules: blocked needs a Blocked by."""
    _work(memory_editor)
    with pytest.raises(RefusedChangeError):
        memory_editor.set_value("RW-1", "State", "blocked")


@pytest.mark.small
def test_set_state_away_from_blocked_lets_go_of_the_blocker(memory_editor, memory_store):
    """Leaving `blocked` clears Blocked by in the same change, which the two rules would otherwise forbid."""
    _work(memory_editor)
    _work(memory_editor, blocked_by="RW-1")
    changed = memory_editor.set_value("RW-2", "State", "open")
    assert (changed.state, changed.blocked_by) == ("open", "")
    assert memory_store.find("RW-2").entry.blocked_by == ""


@pytest.mark.small
def test_close_refuses_an_entry_another_cites(memory_editor):
    """An entry another cites stays."""
    _work(memory_editor)
    _work(memory_editor, blocked_by="RW-1")
    with pytest.raises(RefusedChangeError):
        memory_editor.close("RW-1", commit="abc1234")


@pytest.mark.small
def test_close_returns_the_changelog_line(memory_editor):
    """The line to write names the date, the area, the title, the ID and the commit."""
    _work(memory_editor)
    closed = memory_editor.close("RW-1", commit="abc1234")
    assert closed.changelog_line == "- 2026-10-28 — physics: Fix the step (RW-1, `abc1234`)."


@pytest.mark.small
def test_close_records_the_id_and_removes_the_entry(memory_editor, memory_store):
    """A closed ID stays in the ledger and the entry is gone."""
    _work(memory_editor)
    memory_editor.close("RW-1", commit="abc1234")
    assert memory_store.ledger().is_closed("RW-1")
    with pytest.raises(EntryNotFoundError):
        memory_store.find("RW-1")


@pytest.mark.small
def test_close_takes_the_id_out_of_the_pins(memory_editor, memory_store):
    """A closed entry is no longer pinned."""
    _work(memory_editor)
    memory_editor.pin("RW-1")
    memory_editor.close("RW-1", commit="abc1234")
    assert memory_store.config().pins == ()


@pytest.mark.medium
def test_close_deletes_the_detail_file(editor, store):
    """Closing leaves no detail file behind."""
    _work(editor)
    store.write_detail("RW-1", "# RW-1\n")
    editor.close("RW-1", commit="abc1234")
    assert not store.detail_path("RW-1").exists()


@pytest.mark.small
def test_pin_refuses_a_decision(memory_editor):
    """Pins hold work an agent can take."""
    _work(memory_editor, state="decision")
    with pytest.raises(RefusedChangeError):
        memory_editor.pin("RW-1")


@pytest.mark.small
def test_pin_at_a_position_keeps_the_place(memory_editor):
    """A pin given a position goes there, in the owner's order."""
    _work(memory_editor)
    _work(memory_editor)
    memory_editor.pin("RW-1")
    assert memory_editor.pin("RW-2", position=1) == ("RW-2", "RW-1")


@pytest.mark.small
def test_pin_refuses_an_eleventh_entry_when_the_pins_are_full(memory_editor):
    """The pins hold at most ten entries."""
    _pinned(memory_editor, K_PIN_CEILING)
    eleventh = _work(memory_editor)
    with pytest.raises(RefusedChangeError):
        memory_editor.pin(eleventh.ident)


@pytest.mark.small
def test_unpin_takes_the_id_out_of_the_pins(memory_editor):
    """The pins left are returned in their order."""
    _work(memory_editor)
    _work(memory_editor)
    memory_editor.pin("RW-1")
    memory_editor.pin("RW-2")
    assert memory_editor.unpin("RW-2") == ("RW-1",)


@pytest.mark.small
def test_unpin_of_an_unpinned_id_raises(memory_editor):
    """An ID that is not pinned is not found."""
    _work(memory_editor)
    with pytest.raises(EntryNotFoundError):
        memory_editor.unpin("RW-1")


@pytest.mark.small
def test_move_puts_the_entry_in_the_other_area_and_returns_the_one_it_left(memory_editor, memory_store):
    """An entry moves to another area."""
    _work(memory_editor)
    assert memory_editor.move("RW-1", "BUILD") == "PHYSICS"
    assert memory_store.find("RW-1").area == "BUILD"


@pytest.mark.small
def test_merge_areas_moves_every_entry_and_drops_the_area(memory_editor, memory_store):
    """Merging moves them all and the emptied area leaves the configuration."""
    _work(memory_editor)
    _work(memory_editor, area="BUILD")
    assert memory_editor.merge_areas("PHYSICS", "BUILD") == 1
    assert memory_store.config().areas == ("PHYSICS",)
    assert sorted(entry.ident for entry in memory_store.entries()) == ["RW-1", "RW-2"]


@pytest.mark.small
def test_merge_areas_refuses_an_area_merged_into_itself(memory_editor):
    """An area is not merged into itself."""
    with pytest.raises(RefusedChangeError):
        memory_editor.merge_areas("PHYSICS", "PHYSICS")


@pytest.mark.medium
def test_merge_areas_deletes_the_file_of_the_emptied_area(editor, store):
    """The emptied area's file is gone from the disk."""
    editor.merge_areas("PHYSICS", "BUILD")
    assert not store.area_path("BUILD").exists()


@pytest.mark.parametrize("name", ["Rendering", "BUILD"], ids=["out of shape", "taken"])
@pytest.mark.small
def test_add_area_refuses_a_name_out_of_shape_and_a_taken_one(memory_editor, name):
    """Areas are upper case words joined by _, each once."""
    with pytest.raises(RefusedChangeError):
        memory_editor.add_area(name)


@pytest.mark.small
def test_add_area_returns_the_areas_sorted(memory_editor):
    """The areas come back in order."""
    assert memory_editor.add_area("AUDIO") == ("AUDIO", "BUILD", "PHYSICS")
