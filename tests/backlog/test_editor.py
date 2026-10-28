# test_editor.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests the changes the backlog commands make: add, promote, set, move, close, pins and areas."""

from __future__ import annotations

import pytest

from sushicore.backlog import RefusedChangeError
from sushicore.backlog.errors import EntryNotFoundError

pytestmark = pytest.mark.medium


def _work(editor, area: str = "PHYSICS", **changes):
    """Adds a work entry with default values."""
    values = dict(area=area, priority="P2", title="Fix the step", done_when="it passes")
    values.update(changes)
    return editor.add_work(**values)


def test_add_takes_the_next_id_and_blocked_by_makes_the_entry_blocked(editor):
    """IDs are counted per kind; a block sets the state."""
    assert _work(editor).ident == "RW-1"
    blocked = _work(editor, blocked_by="RW-1")
    assert (blocked.ident, blocked.state) == ("RW-2", "blocked")
    issue = editor.add_issue(area="BUILD", origin="toolchain", symptom="The link fails", workaround="none")
    assert issue.ident == "KI-1"


def test_add_refuses_a_broken_value_and_an_unknown_area_without_writing(editor, store):
    """A refused add writes nothing and takes no number."""
    with pytest.raises(RefusedChangeError):
        _work(editor, title="x" * 91)
    with pytest.raises(RefusedChangeError):
        _work(editor, area="AUDIO")
    assert _work(editor).ident == "RW-1"


def test_add_puts_a_bare_source_in_backticks(editor, store):
    """A path given bare is written as the Source cell writes it."""
    (store.root / "docs" / "design" / "PHYSICS").mkdir()
    entry = _work(editor, source="docs/design/PHYSICS §3")
    assert entry.source == "`docs/design/PHYSICS` §3"


def test_promote_writes_the_new_work_into_the_issue_fix(editor, store):
    """Promoting an issue opens its work entry and points the issue at it."""
    editor.add_issue(area="BUILD", origin="own", symptom="The link fails", workaround="link twice", fix="none, not yet")
    work = editor.promote("KI-1", priority="P1", title="Fix the link", done_when="one link passes")
    assert work.ident == "RW-1"
    assert store.find("KI-1").entry.fix == "RW-1"
    assert store.find("RW-1").area == "BUILD"


def test_set_changes_one_column_and_refuses_a_broken_value(editor, store):
    """`set` rewrites one cell and keeps the rules."""
    _work(editor)
    editor.set_value("RW-1", "Pri", "P0")
    assert store.find("RW-1").entry.priority == "P0"
    with pytest.raises(RefusedChangeError):
        editor.set_value("RW-1", "State", "blocked")


def test_close_refuses_a_cited_entry_and_records_the_id(editor, store):
    """An entry another cites stays; a closed one leaves its ID in the ledger and a changelog line."""
    _work(editor)
    _work(editor, blocked_by="RW-1")
    with pytest.raises(RefusedChangeError):
        editor.close("RW-1", commit="abc1234")
    closed = editor.close("RW-2", commit="abc1234")
    assert closed.changelog_line == "- 2026-10-28 — physics: Fix the step (RW-2, `abc1234`)."
    assert store.ledger().is_closed("RW-2")
    with pytest.raises(EntryNotFoundError):
        store.find("RW-2")


def test_close_deletes_the_detail_and_the_pin(editor, store):
    """Closing leaves nothing behind."""
    _work(editor)
    editor.pin("RW-1")
    store.write_detail("RW-1", "# RW-1\n")
    editor.close("RW-1", commit="abc1234")
    assert not store.detail_path("RW-1").exists()
    assert store.config().pins == ()


def test_pins_refuse_a_decision_and_keep_a_place(editor, store):
    """Pins hold work an agent can take, in the owner's order."""
    _work(editor)
    _work(editor)
    _work(editor, state="decision")
    editor.pin("RW-1")
    assert editor.pin("RW-2", position=1) == ("RW-2", "RW-1")
    with pytest.raises(RefusedChangeError):
        editor.pin("RW-3")
    assert editor.unpin("RW-2") == ("RW-1",)


def test_move_and_merge_areas(editor, store):
    """An entry moves to another area; merging moves them all and deletes the area."""
    _work(editor)
    _work(editor, area="BUILD")
    assert editor.move("RW-1", "BUILD") == "PHYSICS"
    assert store.find("RW-1").area == "BUILD"
    assert editor.merge_areas("PHYSICS", "BUILD") == 2
    assert store.config().areas == ("PHYSICS",)
    assert not store.area_path("BUILD").exists()


def test_add_area_refuses_a_name_out_of_shape_and_a_taken_one(editor):
    """Areas are upper case words joined by _, each once."""
    with pytest.raises(RefusedChangeError):
        editor.add_area("Rendering")
    with pytest.raises(RefusedChangeError):
        editor.add_area("BUILD")
    assert editor.add_area("AUDIO") == ("AUDIO", "BUILD", "PHYSICS")
