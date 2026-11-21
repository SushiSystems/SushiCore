# test_renumber.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests `renumber`: two branches of the backlog that took one ID or conflicted in its counters."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from sushicore.backlog import BacklogRenumberer, check_backlog


def _git(root: Path, *arguments: str, check: bool = True) -> str:
    """Runs git in the repository and returns its output; a failure raises unless *check* is off."""
    completed = subprocess.run(
        ["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t", *arguments],
        capture_output=True, text=True, check=check,
    )
    return completed.stdout


@pytest.mark.medium
def test_renumber_keeps_the_target_branch_entry_and_moves_the_other(editor, store):
    """Two branches that each took RW-1: main keeps it, the side's entry becomes RW-2."""
    root = store.root
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "start")
    _git(root, "checkout", "-q", "-b", "side")
    editor.add_work(area="PHYSICS", priority="P2", title="Side work", done_when="side done")
    _git(root, "commit", "-q", "-am", "side")
    _git(root, "checkout", "-q", "main")
    editor.add_work(area="PHYSICS", priority="P2", title="Main work", done_when="main done")
    _git(root, "commit", "-q", "-am", "main")
    _git(root, "merge", "-q", "side", check=False)
    result = BacklogRenumberer(store, "main").run()
    assert result.renames == (("RW-1", "RW-2"),)
    assert store.find("RW-1").entry.title == "Main work"
    assert store.find("RW-2").entry.title == "Side work"
    assert check_backlog(store) == []


@pytest.mark.medium
def test_renumber_keeps_the_closes_of_both_sides_of_a_conflicted_ledger_and_rewrites_the_index(editor, store):
    """Two branches that each closed an entry conflict in `ids.toml` and in the index; `renumber` resolves both."""
    for title in ("First", "Second", "Third"):
        editor.add_work(area="PHYSICS", priority="P2", title=title, done_when="it is done")
    editor.close("RW-1")
    editor.close("RW-2")
    ids = store.folder / "ids.toml"
    merged = ids.read_text(encoding="utf-8")
    ours, theirs = (merged.replace('closed = "1-2"', f'closed = "{number}"', 1) for number in "12")
    ids.write_text(f"<<<<<<< HEAD\n{ours}=======\n{theirs}>>>>>>> side\n", encoding="utf-8")
    index = store.folder / "README.md"
    index.write_text("<<<<<<< HEAD\nours\n=======\ntheirs\n>>>>>>> side\n", encoding="utf-8")
    BacklogRenumberer(store, "main").run()
    assert store.ledger().closed["RW"] == {1, 2}
    assert "<<<<<<<" not in index.read_text(encoding="utf-8")
    assert check_backlog(store) == []
