# migrate.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Moves a dependency root to another directory behind a journal, with rollback and finalize.

The old path becomes a directory link to the new root. The steps and their order are in
``docs/design/PROVISION.md``, "Phase B: hub's tree moves".
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol, final

from ..errors import SushiCoreError
from .links import is_dir_link, link_target, make_dir_link, remove_dir_link
from .lock import ProvisionLock

#: The journal of a migration that can still be rolled back, kept in the new root.
JOURNAL = ".migrate-journal.jsonl"

#: The name the journal takes once the migration is finalized.
JOURNAL_DONE = ".migrate-journal.done.jsonl"

#: Appended to the old root's name for the copy kept until ``finalize``.
ASIDE_SUFFIX = ".pre-migrate"

#: Appended to a component's name while its copy is not yet verified.
PARTIAL_SUFFIX = ".partial"

#: Free space a copy needs, as a multiple of the bytes it copies.
SPACE_MARGIN = 1.1

_LOCK_FILE = ".lock"

Report = Callable[[str], None]


class MigrationError(SushiCoreError):
    """Reports a migration, rollback or finalize that cannot go on."""


@dataclass(frozen=True, slots=True)
class Move:
    """Holds one top-level component of the old root and where it goes."""

    name: str
    source: Path
    target: Path
    files: int
    bytes: int


@dataclass(frozen=True, slots=True)
class MigrationPlan:
    """Holds what a migration will move and whether the target can take it."""

    old_root: Path
    new_root: Path
    moves: tuple[Move, ...]
    total_bytes: int
    free_bytes: int
    same_volume: bool

    @property
    def enough_space(self) -> bool:
        """Report whether the target volume can take the tree; a rename needs no space."""
        return self.same_volume or self.free_bytes >= self.total_bytes * SPACE_MARGIN

    @property
    def already_migrated(self) -> bool:
        """Report whether the old root is already a link to the new root."""
        return _links_to(self.old_root, self.new_root)


@final
class MigrationJournal:
    """Appends the steps of a migration to a file in the new root and reads them back."""

    def __init__(self, new_root: Path) -> None:
        """Bind the journal to the new root it lives in."""
        self._path = new_root / JOURNAL

    def exists(self) -> bool:
        """Report whether any step was recorded and not yet closed or discarded."""
        return self._path.is_file()

    def append(self, step: str, **fields: object) -> None:
        """Record *step* with its *fields* and flush the line to disk."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps({"step": step, **fields}, ensure_ascii=False)
        with self._path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(line + "\n")
            stream.flush()
            os.fsync(stream.fileno())

    def entries(self) -> list[dict]:
        """Return every recorded step, oldest first; a line cut short by a crash is left out."""
        if not self._path.is_file():
            return []
        entries: list[dict] = []
        for line in self._path.read_text(encoding="utf-8").splitlines():
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            if isinstance(entry, dict) and "step" in entry:
                entries.append(entry)
        return entries

    def names(self, step: str) -> set[str]:
        """Return the component names recorded under *step*."""
        return {str(e.get("name")) for e in self.entries() if e["step"] == step}

    def close(self) -> None:
        """Rename the journal so that a rollback finds nothing to replay."""
        os.replace(self._path, self._path.with_name(JOURNAL_DONE))

    def discard(self) -> None:
        """Delete the journal."""
        self._path.unlink(missing_ok=True)


class _Mover(Protocol):
    """Takes one component to the new root and can take it back."""

    step: str

    def transfer(self, move: Move, journal: MigrationJournal) -> None:
        """Put the component at its target and record ``step``."""

    def undo(self, name: str, old_root: Path, new_root: Path) -> None:
        """Leave the component named *name* at the old root only."""


@final
class _RenameMover:
    """Moves a component with one rename, for two roots on the same volume."""

    step = "moved"

    def transfer(self, move: Move, journal: MigrationJournal) -> None:
        """Rename the component into the new root and record ``moved``.

        Raises:
            MigrationError: The rename failed; a file in use is named as the cause.
        """
        try:
            os.rename(move.source, move.target)
        except PermissionError as error:
            raise MigrationError(
                f"{move.name}: a process still uses a file under {move.source.as_posix()}; "
                f"close it and run the migration again ({error})") from error
        except OSError as error:
            raise MigrationError(f"{move.name}: could not be moved: {error}") from error
        journal.append(self.step, name=move.name)

    def undo(self, name: str, old_root: Path, new_root: Path) -> None:
        """Rename the component back into the old root."""
        moved = new_root / name
        if not _present(moved):
            return
        try:
            os.rename(moved, old_root / name)
        except OSError as error:
            raise MigrationError(f"{name}: could not be moved back: {error}") from error


@final
class _CopyMover:
    """Copies a component, verifies the copy and renames it into place, across volumes."""

    step = "copied"

    def transfer(self, move: Move, journal: MigrationJournal) -> None:
        """Copy the component into the new root and record ``copied`` once it verifies.

        Raises:
            MigrationError: A file could not be read, or the copy differs from the source.
        """
        partial = _partial_path(move.target)
        _remove_tree(partial)
        journal.append("copy-start", name=move.name)
        try:
            _copy_component(move.source, partial)
        except OSError as error:
            _remove_tree(partial)
            journal.append("copy-failed", name=move.name)
            raise MigrationError(f"{move.name}: could not be copied: {error}") from error
        if not _verify_component(move.source, partial):
            _remove_tree(partial)
            journal.append("copy-failed", name=move.name)
            raise MigrationError(
                f"{move.name}: the copy differs from {move.source.as_posix()} "
                "in file count or file size")
        os.rename(partial, move.target)
        journal.append(self.step, name=move.name)

    def undo(self, name: str, old_root: Path, new_root: Path) -> None:
        """Delete the copy, provided the original is still at the old root.

        Raises:
            MigrationError: The old root no longer holds the component.
        """
        copy = new_root / name
        if not _present(copy):
            return
        if not _present(old_root / name):
            raise MigrationError(
                f"{name}: {copy.as_posix()} is the only copy left and was not deleted")
        _remove_tree(copy)


_RENAME: _Mover = _RenameMover()
_COPY: _Mover = _CopyMover()

#: The mover that undoes each journal step a mover records.
_MOVERS: dict[str, _Mover] = {mover.step: mover for mover in (_RENAME, _COPY)}


def plan(old_root: Path, new_root: Path) -> MigrationPlan:
    """Return what moving *old_root* to *new_root* takes, without changing the disk.

    Raises:
        MigrationError: The old root is missing or links elsewhere, one root lies
            inside the other, or the new root already holds a component's name.
    """
    old_root, new_root = _absolute(old_root), _absolute(new_root)
    journal = MigrationJournal(new_root)
    moves: tuple[Move, ...] = ()
    if not _links_to(old_root, new_root):
        _check_roots(old_root, new_root, journal)
        moves = _moves(old_root, new_root, journal)
    return MigrationPlan(
        old_root=old_root,
        new_root=new_root,
        moves=moves,
        total_bytes=sum(move.bytes for move in moves),
        free_bytes=shutil.disk_usage(_existing_ancestor(new_root)).free,
        same_volume=_same_volume(old_root, new_root),
    )


def migrate(plan: MigrationPlan, report: Report) -> None:
    """Move every component of *plan*, set the old root aside and link it to the new root.

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
        mover = _RENAME if plan.same_volume else _COPY
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
    old_root, new_root = _absolute(old_root), _absolute(new_root)
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
    old_root, new_root = _absolute(old_root), _absolute(new_root)
    aside = _aside_path(old_root)
    if not _links_to(old_root, new_root):
        raise MigrationError(
            f"{old_root.as_posix()} is not a link to {new_root.as_posix()}; nothing was deleted")
    if not _present(aside) and not drop_link:
        raise MigrationError(f"{aside.as_posix()} does not exist; nothing was deleted")
    with ProvisionLock(new_root / _LOCK_FILE):
        journal = MigrationJournal(new_root)
        if _present(aside):
            _remove_tree(aside)
            report(f"deleted {aside.as_posix()}")
        if journal.exists():
            journal.append("finalized")
            journal.close()
        if drop_link:
            remove_dir_link(old_root)
            report(f"removed the link at {old_root.as_posix()}")


def _check_roots(old_root: Path, new_root: Path, journal: MigrationJournal) -> None:
    """Raise MigrationError unless *old_root* can be moved to *new_root*."""
    if is_dir_link(old_root):
        raise MigrationError(
            f"{old_root.as_posix()} is a link to {link_target(old_root)}, "
            f"not to {new_root.as_posix()}")
    resumable = journal.exists() and _present(_aside_path(old_root))
    if not old_root.is_dir() and not resumable:
        raise MigrationError(f"{old_root.as_posix()} is not a directory")
    old, new = old_root.resolve(), new_root.resolve()
    if old == new or old in new.parents or new in old.parents:
        raise MigrationError(
            f"{new_root.as_posix()} and {old_root.as_posix()} lie inside one another")


def _moves(old_root: Path, new_root: Path, journal: MigrationJournal) -> tuple[Move, ...]:
    """Return one move per top-level directory of *old_root* not yet transferred.

    Raises:
        MigrationError: The new root already holds an entry of the same name.
    """
    if not old_root.is_dir():
        return ()
    done = set().union(*(journal.names(step) for step in _MOVERS))
    moves: list[Move] = []
    for source in sorted(p for p in old_root.iterdir() if p.is_dir() and p.name not in done):
        target = new_root / source.name
        if _present(target):
            raise MigrationError(
                f"{target.as_posix()} already exists; the migration would overwrite it")
        sizes = _file_sizes(source)
        moves.append(Move(source.name, source, target, len(sizes), sum(sizes.values())))
    return tuple(moves)


def _swap_and_link(
    old_root: Path, new_root: Path, journal: MigrationJournal, report: Report,
) -> None:
    """Rename the old root aside and make a link to the new root in its place.

    Raises:
        MigrationError: The old root could not be renamed, or the link not made.
    """
    aside = _aside_path(old_root)
    if _present(old_root):
        if _present(aside):
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
        if _present(aside) and not _present(old_root):
            os.rename(aside, old_root)
        raise MigrationError(f"{old_root.as_posix()} could not be linked: {error}") from error
    journal.append("linked")
    report(f"linked {old_root.as_posix()} to {new_root.as_posix()}")


def _undo(entry: dict, old_root: Path, new_root: Path, report: Report) -> None:
    """Reverse one journal entry; a step already reversed, or not this module's, is skipped."""
    step, name = entry["step"], str(entry.get("name", ""))
    aside = _aside_path(old_root)
    if step == "linked" and is_dir_link(old_root):
        remove_dir_link(old_root)
        report(f"removed the link at {old_root.as_posix()}")
    elif step == "aside" and _present(aside) and not _present(old_root):
        os.rename(aside, old_root)
        report(f"restored {old_root.as_posix()}")
    elif step == "copy-start":
        _remove_tree(_partial_path(new_root / name))
    elif step in _MOVERS:
        _MOVERS[step].undo(name, old_root, new_root)
        report(f"restored {name}")


def _copy_component(source: Path, target: Path) -> None:
    """Copy the tree at *source* to *target*, recreating links instead of following them."""
    if is_dir_link(source):
        make_dir_link(target, link_target(source))
        return
    junctions: list[Path] = []

    def skip_junctions(folder: str, names: list[str]) -> list[str]:
        """Return the names copytree must leave out, which are the junctions."""
        found = [n for n in names if _is_junction_only(Path(folder) / n)]
        junctions.extend(Path(folder) / n for n in found)
        return found

    shutil.copytree(source, target, symlinks=True, ignore=skip_junctions)
    for junction in junctions:
        make_dir_link(target / junction.relative_to(source), link_target(junction))


def _verify_component(source: Path, copy: Path) -> bool:
    """Report whether *copy* holds the same files as *source*, each of the same size."""
    return _file_sizes(source) == _file_sizes(copy)


def _file_sizes(root: Path) -> dict[str, int]:
    """Return the size of every file under *root* by relative path, a link counting as 0."""
    if is_dir_link(root):
        return {"": 0}
    sizes: dict[str, int] = {}
    prefix = len(str(root)) + 1
    pending = [str(root)]
    while pending:
        with os.scandir(pending.pop()) as entries:
            for entry in entries:
                key = entry.path[prefix:].replace(os.sep, "/")
                if entry.is_symlink():
                    sizes[key] = 0
                elif entry.is_dir(follow_symlinks=False):
                    if is_dir_link(Path(entry.path)):
                        sizes[key] = 0
                    else:
                        pending.append(entry.path)
                else:
                    sizes[key] = entry.stat(follow_symlinks=False).st_size
    return sizes


def _remove_tree(path: Path) -> None:
    """Delete *path* whatever it is: a link alone, or a tree with its read-only files."""
    if is_dir_link(path):
        remove_dir_link(path)
    elif path.is_dir():
        if sys.version_info >= (3, 12):
            shutil.rmtree(path, onexc=_clear_read_only)
        else:
            shutil.rmtree(path, onerror=_clear_read_only)
    elif path.exists():
        path.unlink()


def _clear_read_only(function: Callable[[str], None], path: str, _error: object) -> None:
    """Make *path* writable and repeat the removal that failed on it."""
    os.chmod(path, stat.S_IWRITE | stat.S_IREAD)
    function(path)


def _is_junction_only(path: Path) -> bool:
    """Report whether *path* is a directory link that is not a symlink."""
    return is_dir_link(path) and not path.is_symlink()


def _links_to(link: Path, target: Path) -> bool:
    """Report whether *link* is a directory link whose target is *target*."""
    found = link_target(link)
    return found is not None and found.resolve() == target.resolve()


def _present(path: Path) -> bool:
    """Report whether *path* exists, a link with a missing target included."""
    return path.exists() or is_dir_link(path)


def _absolute(path: Path) -> Path:
    """Return *path* as an absolute path without resolving a link."""
    return Path(os.path.abspath(path))


def _aside_path(old_root: Path) -> Path:
    """Return where the old root is kept until ``finalize``."""
    return old_root.with_name(old_root.name + ASIDE_SUFFIX)


def _partial_path(target: Path) -> Path:
    """Return where a component is copied before it is verified."""
    return target.with_name(target.name + PARTIAL_SUFFIX)


def _existing_ancestor(path: Path) -> Path:
    """Return *path*, or the nearest directory above it that exists."""
    current = _absolute(path)
    while not current.exists() and current != current.parent:
        current = current.parent
    return current


def _same_volume(old_root: Path, new_root: Path) -> bool:
    """Report whether the two roots are on one volume, so a rename can move between them."""
    old_device = os.stat(_existing_ancestor(old_root)).st_dev
    return old_device == os.stat(_existing_ancestor(new_root)).st_dev
