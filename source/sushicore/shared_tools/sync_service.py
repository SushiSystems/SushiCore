# sync_service.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Copies the shared tools of one SushiCore tag into a repository and locks them."""

from __future__ import annotations

from collections.abc import Callable, Collection, Iterable
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import final

from .errors import LocalEditsError
from .git_reader import GitReader, tracked_files
from .header_merger import HeaderMerger, first_year
from .licence_toolkit import load_toolkit
from .lock_file import SharedToolsLock, digest
from .pre_move_digests import PreMoveDigests, is_pre_move_copy, read_pre_move_digests
from .readme_rows import merge_readme
from .settings_reads import missing_settings

K_TOOLS = "tools"
ReadmeMerger = Callable[[str | None, str, Collection[str]], str]
SettingsReporter = Callable[[Iterable[str], str | None, str | None], dict[str, str | None]]
PreMoveReader = Callable[[], PreMoveDigests]
K_README = "tools/README.md"
K_SETTINGS = "tools/settings.py"
K_COMMUNITY = (".github/CODE_OF_CONDUCT.md", ".github/SECURITY.md")
#: The files of SushiCore's `tools/` that belong to SushiCore alone and are never copied.
K_EXCLUDED = frozenset(
    {
        "tools/known_findings.toml",
        "tools/settings.py",
        "tools/README.md",
        "tools/layering/check_package_layers.py",
        "tools/provision/check_config_reads.py",
        "tools/tests/test_check_package_layers.py",
        "tools/tests/test_check_config_reads.py",
    }
)


@final
@dataclass(frozen=True, slots=True)
class SyncResult:
    """What a sync did: the files written, the files dropped, the lock and the missing settings.

    The missing settings are the ones the copied tools read that `tools/settings.py` lacks, each
    with its value in SushiCore.
    """

    written: list[str]
    dropped: list[str]
    lock: SharedToolsLock
    missing_settings: dict[str, str | None] = field(default_factory=dict)


@final
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
        merge_readme: ReadmeMerger = merge_readme,
        missing_settings: SettingsReporter = missing_settings,
        pre_move: PreMoveReader = read_pre_move_digests,
    ) -> None:
        """Stores the source, the target, the options and the three collaborators of the sync.

        Args:
            merge_readme: Returns the README text holding the shared rows, from the README the
                repository holds, the one of the tag and the shared paths.
            missing_settings: Returns the settings the tools read that the repository lacks, from
                the tool texts, the repository's settings text and the tag's settings text.
            pre_move: Returns the digests of each file as SushiSkills held it before the move; a
                file that equals one is stale, not a local edit.
        """
        self._reader = reader
        self._root = root
        self._tag = tag
        self._keep = frozenset(keep)
        self._force = force
        self._dry_run = dry_run
        self._merge_readme = merge_readme
        self._missing_settings = missing_settings
        self._pre_move = pre_move
        self._texts: dict[str, str] = {}

    def run(self) -> SyncResult:
        """Writes every shared file that differs, then the lock; a dry run writes neither.

        Raises LocalEditsError, with nothing written, when a file holds a local edit and force is off.
        """
        commit = self._reader.commit(self._tag)
        self._texts = self._reader.snapshot(self._tag, K_TOOLS, *K_COMMUNITY)
        everything = self._shared(self._reader.files(self._tag, K_TOOLS, *K_COMMUNITY))
        copied = [path for path in everything if path not in self._keep]
        dropped = self._dropped(everything)
        with load_toolkit(self._reader, self._tag) as toolkit:
            merger = HeaderMerger(toolkit, self._root)
            wanted = {path: self._wanted(merger, path) for path in copied}
            pending = [path for path in copied if wanted[path] is not None]
            pre_move = self._pre_move()
            edited = [] if self._force else [path for path in pending if self._is_edit(merger, path, pre_move)]
        if edited:
            raise LocalEditsError(edited)
        lock = SharedToolsLock(self._tag, commit, {path: self._digest(path, wanted[path]) for path in copied})
        readme = self._readme(everything)
        if not self._dry_run:
            self._write(pending, wanted)
            if readme is not None:
                self._write_text(self._root / K_README, readme)
            lock.write(self._root)
        written = [*pending, K_README] if readme is not None else pending
        return SyncResult(written, dropped, lock, self._settings_lacking(copied))

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
        text = self._texts.get(path, "")
        year = first_year(date.today().year, current, text)
        text = merger.merged(path, text, current, year)
        return None if text == current else text

    def _is_edit(self, merger: HeaderMerger, path: str, pre_move: PreMoveDigests) -> bool:
        """Returns whether the file's text is one no release of the tools, and no pre-move copy, held."""
        current = _read(self._root / path)
        if current is None:
            return False
        body = merger.body(path, current)
        known = {merger.body(path, text) for text in self._reader.history(self._tag, path)}
        return body not in known and not is_pre_move_copy(pre_move, path, body)

    def _digest(self, path: str, wanted: str | None) -> str:
        """Returns the hash of the bytes the file holds once the sync is done."""
        if wanted is None:
            return digest((self._root / path).read_bytes())
        return digest(wanted.encode("utf-8"))

    def _readme(self, shared: list[str]) -> str | None:
        """Returns the README text with the shared rows, or None when no write is needed."""
        source = self._texts.get(K_README)
        if source is None or K_README in self._keep:
            return None
        current = _read(self._root / K_README)
        merged = self._merge_readme(current, source, shared)
        return None if merged == current else merged

    def _settings_lacking(self, copied: list[str]) -> dict[str, str | None]:
        """Returns the settings the copied Python tools read that the repository does not define."""
        python = [path for path in copied if path.endswith(".py")]
        texts = (self._texts.get(path, "") for path in python)
        core = self._texts.get(K_SETTINGS)
        return self._missing_settings(texts, _read(self._root / K_SETTINGS), core)

    def _write(self, pending: list[str], wanted: dict[str, str | None]) -> None:
        """Writes each pending file."""
        for path in pending:
            self._write_text(self._root / path, wanted[path] or "")

    @staticmethod
    def _write_text(target: Path, text: str) -> None:
        """Writes a text file with LF newlines, creating its folder."""
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8", newline="\n")


def _read(path: Path) -> str | None:
    """Returns a file's text, or None when it does not exist."""
    return path.read_text(encoding="utf-8") if path.is_file() else None
