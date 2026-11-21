# command_context.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What every `backlog` command shares: where the repository is, how a result is printed and which entries are unverified."""

from __future__ import annotations

import datetime
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any, final

from .model import IssueEntry, WorkEntry
from .order import age, is_late
from .store import AnyEntry, BacklogStore, Located

K_NO_STAMP = "no verification stamp exists; run tools/check_all.py to write one"
K_UNVERIFIED = " unverified"


def json_option() -> Any:
    """Returns the `--json` option of a command that can print its result as JSON."""
    import typer

    return typer.Option(False, "--json", help="Print JSON, for an agent.")


def shown_path(path: Path, root: Path) -> str:
    """Returns a path from the root when it is under it."""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def entry_payload(item: Located, today: datetime.date) -> dict:
    """Returns an entry as a JSON object: its columns, its area, and for work its age."""
    entry = item.entry
    payload: dict = dict(zip(entry.COLUMNS, entry.cells()))
    payload["Kind"] = "work" if isinstance(entry, WorkEntry) else "issue"
    payload["Area"] = item.area
    payload["Age"] = age(entry, today)
    if isinstance(entry, WorkEntry):
        payload["Late"] = is_late(entry, today)
    return payload


def entry_line(entry: AnyEntry, today: datetime.date) -> str:
    """Returns one entry as a line of text."""
    if isinstance(entry, IssueEntry):
        return f"{entry.ident} {entry.origin}: {entry.symptom}"
    late = " late" if is_late(entry, today) else ""
    return f"{entry.ident} {entry.priority} {entry.state}{late} {age(entry, today)}d: {entry.title}"


def is_unverified(entry: AnyEntry, ids: frozenset[str]) -> bool:
    """Returns whether an open work entry is named after the verification stamp."""
    return isinstance(entry, WorkEntry) and entry.state == "open" and entry.ident in ids


@final
class CommandContext:
    """The repository, the printing and the stamp a command reads, held once for the whole group."""

    def __init__(
        self,
        *,
        program: str,
        project_root: Callable[[], Path],
        report: Callable[[str], None],
        unverified: Callable[[Path], frozenset[str] | None],
    ) -> None:
        """Keeps the program name for examples, the root, the printer and the stamp reader."""
        self.program = program
        self.project_root = project_root
        self.report = report
        self._unverified = unverified

    def store(self) -> BacklogStore:
        """Returns the store of the repository the CLI runs in."""
        return BacklogStore(self.project_root())

    def emit(self, payload: object, lines: list[str], as_json: bool) -> None:
        """Prints the result as JSON or as lines."""
        if as_json:
            self.report(json.dumps(payload, indent=2))
        else:
            for line in lines:
                self.report(line)

    def emit_entries(self, chosen: list[Located], empty: str, as_json: bool) -> None:
        """Prints entries with the unverified mark, and the no-stamp line when there is no stamp."""
        today = self.store().today()
        marked = self._unverified(self.project_root())
        ids = marked or frozenset()
        payload = [{**entry_payload(item, today), "Unverified": is_unverified(item.entry, ids)} for item in chosen]
        lines = [entry_line(item.entry, today) + (K_UNVERIFIED if is_unverified(item.entry, ids) else "")
                 for item in chosen] or ([empty] if empty else [])
        if marked is None:
            lines.append(K_NO_STAMP)
        self.emit(payload, lines, as_json)
