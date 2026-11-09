# migration_plan.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Reads the disk and works out what a migration moves, without changing anything."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .links import is_dir_link, link_target
from .migration_disk import absolute, aside_path, existing_ancestor, file_sizes, is_present, same_volume
from .migration_error import MigrationError
from .migration_journal import TRANSFER_STEPS, MigrationJournal


#: Free space a copy needs, as a multiple of the bytes it copies.
SPACE_MARGIN = 1.1


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
        return links_to(self.old_root, self.new_root)


@dataclass(frozen=True, slots=True)
class PlanProbes:
    """Holds the reads :func:`plan` makes of the disk, each replaceable by a test.

    Every default looks its function up when called.

    Attributes:
        is_link: Reports whether a path is a directory link.
        link_target: Gives the directory a link points to, or None for a path that is no link.
        is_dir: Reports whether a path is a directory.
        present: Reports whether a path exists, a link with a missing target included.
        resolve: Gives a path with its links followed.
        subfolders: Lists the folders directly below a path.
        file_sizes: Gives the size of every file under a folder by relative path.
        free_bytes: Gives the free space on the volume holding a path.
        same_volume: Reports whether two roots are on one volume.
        journal_exists: Reports whether a migration journal sits in a root.
    """

    is_link: Callable[[Path], bool] = lambda path: is_dir_link(path)
    link_target: Callable[[Path], Path | None] = lambda path: link_target(path)
    is_dir: Callable[[Path], bool] = lambda path: path.is_dir()
    present: Callable[[Path], bool] = lambda path: is_present(path)
    resolve: Callable[[Path], Path] = lambda path: path.resolve()
    subfolders: Callable[[Path], list[Path]] = lambda path: sorted(
        p for p in path.iterdir() if p.is_dir())
    file_sizes: Callable[[Path], dict[str, int]] = lambda path: file_sizes(path)
    free_bytes: Callable[[Path], int] = lambda path: shutil.disk_usage(
        existing_ancestor(path)).free
    same_volume: Callable[[Path, Path], bool] = lambda old, new: same_volume(old, new)
    journal_exists: Callable[[Path], bool] = lambda root: MigrationJournal(root).exists()



def plan(old_root: Path, new_root: Path, probes: PlanProbes | None = None) -> MigrationPlan:
    """Return what moving *old_root* to *new_root* takes, without changing the disk.

    Args:
        probes: The disk reads to make; the real ones when ``None``.

    Raises:
        MigrationError: The old root is missing or links elsewhere, one root lies
            inside the other, or the new root already holds a component's name.
    """
    probes = probes or PlanProbes()
    old_root, new_root = absolute(old_root), absolute(new_root)
    journal = MigrationJournal(new_root)
    moves: tuple[Move, ...] = ()
    if not links_to(old_root, new_root, probes):
        _check_roots(old_root, new_root, journal, probes)
        moves = _moves(old_root, new_root, journal, probes)
    return MigrationPlan(
        old_root=old_root,
        new_root=new_root,
        moves=moves,
        total_bytes=sum(move.bytes for move in moves),
        free_bytes=probes.free_bytes(new_root),
        same_volume=probes.same_volume(old_root, new_root),
    )


def _check_roots(old_root: Path, new_root: Path, journal: MigrationJournal,
                 probes: PlanProbes) -> None:
    """Raise MigrationError unless *old_root* can be moved to *new_root*."""
    if probes.is_link(old_root):
        raise MigrationError(
            f"{old_root.as_posix()} is a link to {probes.link_target(old_root)}, "
            f"not to {new_root.as_posix()}")
    resumable = probes.journal_exists(new_root) and probes.present(aside_path(old_root))
    if not probes.is_dir(old_root) and not resumable:
        raise MigrationError(f"{old_root.as_posix()} is not a directory")
    old, new = probes.resolve(old_root), probes.resolve(new_root)
    if old == new or old in new.parents or new in old.parents:
        raise MigrationError(
            f"{new_root.as_posix()} and {old_root.as_posix()} lie inside one another")


def _moves(old_root: Path, new_root: Path, journal: MigrationJournal,
           probes: PlanProbes) -> tuple[Move, ...]:
    """Return one move per top-level directory of *old_root* not yet transferred.

    Raises:
        MigrationError: The new root already holds an entry of the same name.
    """
    if not probes.is_dir(old_root):
        return ()
    done = set().union(*(journal.names(step) for step in TRANSFER_STEPS))
    moves: list[Move] = []
    for source in (p for p in probes.subfolders(old_root) if p.name not in done):
        target = new_root / source.name
        if probes.present(target):
            raise MigrationError(
                f"{target.as_posix()} already exists; the migration would overwrite it")
        sizes = probes.file_sizes(source)
        moves.append(Move(source.name, source, target, len(sizes), sum(sizes.values())))
    return tuple(moves)


def links_to(link: Path, target: Path, probes: PlanProbes | None = None) -> bool:
    """Report whether *link* is a directory link whose target is *target*."""
    probes = probes or PlanProbes()
    found = probes.link_target(link)
    return found is not None and probes.resolve(found) == probes.resolve(target)
