# migration_movers.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The two ways a migration takes a component to the new root, and takes it back."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Protocol, final

from .migration_disk import copy_component, is_present, partial_path, remove_tree, verify_component
from .migration_error import MigrationError
from .migration_journal import MigrationJournal
from .migration_plan import Move


class Mover(Protocol):
    """Takes one component to the new root and can take it back."""

    step: str

    def transfer(self, move: Move, journal: MigrationJournal) -> None:
        """Put the component at its target and record ``step``."""

    def undo(self, name: str, old_root: Path, new_root: Path) -> None:
        """Leave the component named *name* at the old root only."""


@final
class RenameMover:
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
        if not is_present(moved):
            return
        try:
            os.rename(moved, old_root / name)
        except OSError as error:
            raise MigrationError(f"{name}: could not be moved back: {error}") from error


@final
class CopyMover:
    """Copies a component, verifies the copy and renames it into place, across volumes.

    Args:
        verify: Reports whether a copy holds the same files as its source; the file-size
            comparison when ``None``.
    """

    step = "copied"

    def __init__(self, verify: Callable[[Path, Path], bool] | None = None) -> None:
        """Store the verifier."""
        self._verify = verify or (lambda source, copy: verify_component(source, copy))

    def transfer(self, move: Move, journal: MigrationJournal) -> None:
        """Copy the component into the new root and record ``copied`` once it verifies.

        Raises:
            MigrationError: A file could not be read, or the copy differs from the source.
        """
        partial = partial_path(move.target)
        remove_tree(partial)
        journal.append("copy-start", name=move.name)
        try:
            copy_component(move.source, partial)
        except OSError as error:
            remove_tree(partial)
            journal.append("copy-failed", name=move.name)
            raise MigrationError(f"{move.name}: could not be copied: {error}") from error
        if not self._verify(move.source, partial):
            remove_tree(partial)
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
        if not is_present(copy):
            return
        if not is_present(old_root / name):
            raise MigrationError(
                f"{name}: {copy.as_posix()} is the only copy left and was not deleted")
        remove_tree(copy)


RENAME: Mover = RenameMover()
COPY: Mover = CopyMover()

#: The mover that undoes each journal step a mover records.
MOVERS: dict[str, Mover] = {mover.step: mover for mover in (RENAME, COPY)}
