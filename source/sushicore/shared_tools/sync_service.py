# sync_service.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Copies the shared tools of one SushiCore tag into a repository and locks them."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .errors import LocalEditsError
from .git_reader import GitReader, tracked_files
from .header_merger import HeaderMerger, first_year
from .licence_toolkit import load_toolkit
from .lock_file import SharedToolsLock, digest

K_TOOLS = "tools"
K_COMMUNITY = (".github/CODE_OF_CONDUCT.md", ".github/SECURITY.md")
#: The files of SushiCore's `tools/` that belong to SushiCore alone and are never copied.
K_EXCLUDED = frozenset({"tools/known_findings.toml", "tools/settings.py", "tools/README.md"})


@dataclass(frozen=True, slots=True)
class SyncResult:
    """What a sync did: the files it wrote or would write, the files upstream dropped, and the lock."""

    written: list[str]
    dropped: list[str]
    lock: SharedToolsLock


class SharedToolsSync:
    """Brings one repository's shared tools to the state of a SushiCore tag."""

    def __init__(
        self,
        reader: GitReader,
        root: Path,
        tag: str,
        *,
        keep: Iterable[str] = (),
        force: bool = False,
        dry_run: bool = False,
    ) -> None:
        """Stores the source, the target and the options of the sync."""
        self._reader = reader
        self._root = root
        self._tag = tag
        self._keep = frozenset(keep)
        self._force = force
        self._dry_run = dry_run

    def run(self) -> SyncResult:
        """Writes every shared file that differs, then the lock; a dry run writes neither.

        Raises LocalEditsError, with nothing written, when a file holds a local edit and force is off.
        """
        commit = self._reader.commit(self._tag)
        everything = self._shared(self._reader.files(self._tag, K_TOOLS, *K_COMMUNITY))
        copied = [path for path in everything if path not in self._keep]
        dropped = self._dropped(everything)
        with load_toolkit(self._reader, self._tag) as toolkit:
            merger = HeaderMerger(toolkit, self._root)
            wanted = {path: self._wanted(merger, path) for path in copied}
            pending = [path for path in copied if wanted[path] is not None]
            edited = [] if self._force else [path for path in pending if self._is_edit(merger, path)]
        if edited:
            raise LocalEditsError(edited)
        lock = SharedToolsLock(self._tag, commit, {path: self._digest(path, wanted[path]) for path in copied})
        if not self._dry_run:
            self._write(pending, wanted)
            lock.write(self._root)
        return SyncResult(pending, dropped, lock)

    @staticmethod
    def _shared(listed: Iterable[str]) -> list[str]:
        """Returns the listed files that are shared, in path order."""
        return sorted(path for path in listed if path not in K_EXCLUDED)

    def _dropped(self, shared: list[str]) -> list[str]:
        """Returns the tracked files an earlier release shared and this one no longer does."""
        held = set(tracked_files(self._root, K_TOOLS, *K_COMMUNITY))
        once = set(self._reader.ever_files(self._tag, K_TOOLS, *K_COMMUNITY)) - K_EXCLUDED
        return sorted((held & once) - set(shared))

    def _wanted(self, merger: HeaderMerger, path: str) -> str | None:
        """Returns the text the repository should hold for a file, or None when it already does."""
        current = _read(self._root / path)
        text = self._reader.show(self._tag, path) or ""
        year = first_year(date.today().year, current, text)
        text = merger.merged(path, text, current, year)
        return None if text == current else text

    def _is_edit(self, merger: HeaderMerger, path: str) -> bool:
        """Returns whether the file's text is one no release of the tools ever held."""
        current = _read(self._root / path)
        if current is None:
            return False
        known = {merger.body(path, text) for text in self._reader.history(self._tag, path)}
        return merger.body(path, current) not in known

    def _digest(self, path: str, wanted: str | None) -> str:
        """Returns the hash of the bytes the file holds once the sync is done."""
        if wanted is None:
            return digest((self._root / path).read_bytes())
        return digest(wanted.encode("utf-8"))

    def _write(self, pending: list[str], wanted: dict[str, str | None]) -> None:
        """Writes each pending file."""
        for path in pending:
            target = self._root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(wanted[path] or "", encoding="utf-8", newline="\n")


def _read(path: Path) -> str | None:
    """Returns a file's text, or None when it does not exist."""
    return path.read_text(encoding="utf-8") if path.is_file() else None
