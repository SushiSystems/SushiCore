# migrate.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Moves a dependency root to another directory behind a journal, with rollback and finalize.

The old path becomes a directory link to the new root. The steps and their order are in
``docs/design/PROVISION/README.md``, "Phase B: hub's tree moves".
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

from .links import is_dir_link, make_dir_link, remove_dir_link
from .lock import ProvisionLock
from .migration_disk import (
    ASIDE_SUFFIX,
    PARTIAL_SUFFIX,
    absolute,
    aside_path,
    is_present,
    partial_path,
    remove_tree,
)
from .migration_error import MigrationError
from .migration_journal import JOURNAL, JOURNAL_DONE, MigrationJournal
from .migration_movers import MOVERS, RENAME, CopyMover
from .migration_plan import SPACE_MARGIN, MigrationPlan, Move, PlanProbes, links_to, plan

_LOCK_FILE = ".lock"

Report = Callable[[str], None]

__all__ = [
    "ASIDE_SUFFIX", "JOURNAL", "JOURNAL_DONE", "PARTIAL_SUFFIX", "SPACE_MARGIN", "MigrationError",
    "MigrationJournal", "MigrationPlan", "Move", "PlanProbes", "Report", "finalize", "migrate",
    "plan", "rollback",
]


def migrate(plan: MigrationPlan, report: Report,
            verify: Callable[[Path, Path], bool] | None = None) -> None:
    """Move every component of *plan*, set the old root aside and link it to the new root.

    Args:
        verify: Reports whether a copy holds the same files as its source; the file-size
            comparison when ``None``.

    A run that stopped part-way goes on from its journal. An old root that already
    links to the new root is reported and left alone.

    Raises:
        MigrationError: Space is short, a component could not be moved or its copy
            differs, or the old root could not be set aside or linked.
    """
    if plan.already_migrated:
        report(f"already migrated: {plan.old_root.as_posix()} links to "
               f"{plan.new_root.as_posix()}")
        return
    if not plan.enough_space:
        needed = int(plan.total_bytes * SPACE_MARGIN)
        raise MigrationError(
            f"not enough space under {plan.new_root.as_posix()}: "
            f"{needed} bytes needed, {plan.free_bytes} bytes free")
    plan.new_root.mkdir(parents=True, exist_ok=True)
    with ProvisionLock(plan.new_root / _LOCK_FILE):
        journal = MigrationJournal(plan.new_root)
        mover = RENAME if plan.same_volume else CopyMover(verify)
        done = journal.names(mover.step)
        for move in plan.moves:
            if move.name in done:
                continue
            mover.transfer(move, journal)
            report(f"{mover.step} {move.name}")
        _swap_and_link(plan.old_root, plan.new_root, journal, report)


def rollback(old_root: Path, new_root: Path, report: Report) -> None:
    """Undo a migration from its journal, newest step first, then delete the journal.

    Raises:
        MigrationError: A step could not be undone; the journal is kept for another run.
    """
    old_root, new_root = absolute(old_root), absolute(new_root)
    journal = MigrationJournal(new_root)
    if not journal.exists():
        report("nothing to roll back")
        return
    with ProvisionLock(new_root / _LOCK_FILE):
        for entry in reversed(journal.entries()):
            _undo(entry, old_root, new_root, report)
        journal.discard()
    report(f"rolled back: {old_root.as_posix()} is the dependency root again")


def finalize(old_root: Path, new_root: Path, report: Report, drop_link: bool = False) -> None:
    """Delete the copy set aside by a migration, and the link too when *drop_link* is set.

    Raises:
        MigrationError: The old root does not link to the new root, or there is no
            copy left to delete and the link was not asked to go.
    """
    old_root, new_root = absolute(old_root), absolute(new_root)
    aside = aside_path(old_root)
    if not links_to(old_root, new_root):
        raise MigrationError(
            f"{old_root.as_posix()} is not a link to {new_root.as_posix()}; nothing was deleted")
    if not is_present(aside) and not drop_link:
        raise MigrationError(f"{aside.as_posix()} does not exist; nothing was deleted")
    with ProvisionLock(new_root / _LOCK_FILE):
        journal = MigrationJournal(new_root)
        if is_present(aside):
            remove_tree(aside)
            report(f"deleted {aside.as_posix()}")
        if journal.exists():
            journal.append("finalized")
            journal.close()
        if drop_link:
            remove_dir_link(old_root)
            report(f"removed the link at {old_root.as_posix()}")



def _swap_and_link(
    old_root: Path, new_root: Path, journal: MigrationJournal, report: Report,
) -> None:
    """Rename the old root aside and make a link to the new root in its place.

    Raises:
        MigrationError: The old root could not be renamed, or the link not made.
    """
    aside = aside_path(old_root)
    if is_present(old_root):
        if is_present(aside):
            raise MigrationError(
                f"{aside.as_posix()} already exists; finalize or remove it first")
        try:
            os.rename(old_root, aside)
        except OSError as error:
            raise MigrationError(
                f"{old_root.as_posix()} could not be set aside; a process may still "
                f"use a file under it ({error})") from error
        journal.append("aside")
    try:
        make_dir_link(old_root, new_root)
    except OSError as error:
        if is_present(aside) and not is_present(old_root):
            os.rename(aside, old_root)
        raise MigrationError(f"{old_root.as_posix()} could not be linked: {error}") from error
    journal.append("linked")
    report(f"linked {old_root.as_posix()} to {new_root.as_posix()}")


def _undo(entry: dict, old_root: Path, new_root: Path, report: Report) -> None:
    """Reverse one journal entry; a step already reversed, or not this module's, is skipped."""
    step, name = entry["step"], str(entry.get("name", ""))
    aside = aside_path(old_root)
    if step == "linked" and is_dir_link(old_root):
        remove_dir_link(old_root)
        report(f"removed the link at {old_root.as_posix()}")
    elif step == "aside" and is_present(aside) and not is_present(old_root):
        os.rename(aside, old_root)
        report(f"restored {old_root.as_posix()}")
    elif step == "copy-start":
        remove_tree(partial_path(new_root / name))
    elif step in MOVERS:
        MOVERS[step].undo(name, old_root, new_root)
        report(f"restored {name}")
