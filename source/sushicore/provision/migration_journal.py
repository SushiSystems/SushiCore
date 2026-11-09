# migration_journal.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The journal a migration appends to, so that a stopped run goes on and a rollback replays."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import final


#: The journal of a migration that can still be rolled back, kept in the new root.
JOURNAL = ".migrate-journal.jsonl"

#: The name the journal takes once the migration is finalized.
JOURNAL_DONE = ".migrate-journal.done.jsonl"

#: The journal steps a mover records once a component is at its target.
TRANSFER_STEPS = ("moved", "copied")


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
