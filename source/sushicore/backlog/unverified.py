# unverified.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Judges which backlog IDs are unverified, from the commits after the stamp.

The rule is in `docs/design/BACKLOG/README.md`.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import final

K_TRAILER = re.compile(r"^Backlog:[ \t]*(.*?)[ \t]*$", re.MULTILINE)
K_ID = re.compile(r"[A-Z]+-\d+")
K_BOOKKEEPING = ("docs/backlog/", "docs/reference/CHANGELOG.md")


@final
@dataclass(frozen=True, slots=True)
class Commit:
    """A commit after the stamp: its message and the paths it changed."""

    message: str
    files: tuple[str, ...] = ()

    def is_bookkeeping(self) -> bool:
        """Returns whether the commit changed nothing but the backlog and the changelog.

        Such a commit files, records or closes entries and carries no work to verify. A commit
        that lists no path counts as work.
        """
        return bool(self.files) and all(path.startswith(K_BOOKKEEPING) for path in self.files)


def unverified_ids(commits: Iterable[Commit]) -> frozenset[str]:
    """Returns the IDs that the `Backlog:` lines of the commits that carry work name.

    An item is an ID when it is one and nothing else: an entry of a sibling, written with its
    repository, and an ID inside the reason of `none (...)` name no entry here.

    Args:
        commits: The commits after the verified commit.
    """
    return frozenset(
        ident
        for commit in commits
        if not commit.is_bookkeeping()
        for line in K_TRAILER.findall(commit.message)
        for ident in (item.strip() for item in line.split(","))
        if K_ID.fullmatch(ident)
    )
