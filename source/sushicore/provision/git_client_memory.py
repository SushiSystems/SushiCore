# git_client_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""A git client that clones from a table of known tags and runs no git."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Mapping

from .git_client import IGitClient


class InMemoryGitClient(IGitClient):
    """Clones the tags it was told about, leaves HEAD at the tag's commit and records each clone.

    It writes nothing: a clone is a record and a HEAD held in memory. A test that needs a
    checkout on disk hands in *materialize*. A clone of a tag that is neither in the table nor
    covered by *commit*, or of any tag when *clones* is false, fails and is not materialized.

    Args:
        tags: The commit each ``(url, tag)`` points at.
        commit: The commit every tag outside the table points at; ``None`` makes them fail.
        clones: Whether clones succeed at all.
        heads: HEADs of checkouts that exist already, by folder.
        default_head: The HEAD of every checkout not listed in *heads* or made by a clone;
            '' says git cannot tell.
        materialize: Called with the destination of each successful, non-dry clone.
    """

    def __init__(self, tags: Mapping[tuple[str, str], str] | None = None, *,
                 commit: str | None = None, clones: bool = True,
                 heads: Mapping[Path, str] | None = None, default_head: str = "",
                 materialize: Callable[[Path], None] | None = None) -> None:
        """Hold the tag table, the fallback commit, the clone switch and the fixed HEADs."""
        self._materialize = materialize
        self._tags = dict(tags or {})
        self._commit = commit
        self._clones = clones
        self._heads = {path.resolve(): head for path, head in (heads or {}).items()}
        self._default_head = default_head
        self.calls: list[tuple[str, str, Path, bool]] = []

    def clone_tag(self, url: str, tag: str, destination: Path, dry_run: bool) -> bool:
        """Record the clone; unless *dry_run*, set the HEAD of *destination* and materialize it."""
        self.calls.append((url, tag, destination, dry_run))
        landed = self._tags.get((url, tag), self._commit)
        if not self._clones or landed is None:
            return False
        if dry_run:
            return True
        self._heads[destination.resolve()] = landed
        if self._materialize is not None:
            self._materialize(destination)
        return True

    def head(self, checkout: Path) -> str:
        """Return the lower-case HEAD of *checkout*, or '' when it has none."""
        return self._heads.get(checkout.resolve(), self._default_head).lower()
