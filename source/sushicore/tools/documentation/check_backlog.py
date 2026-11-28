# check_backlog.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Checks docs/backlog/ against the backlog format of the documentation skill, through the tooling package.

Usage: python -m sushicore.tools.documentation.check_backlog [repository root] [--report] [--rule NAME]

The rules are those of `backlog check` in the tooling package's backlog module, the tool that writes the store.
"""

from __future__ import annotations

import sys
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType


from sushicore.tools.checking.checker import Checker, Issue, run  # noqa: E402
from sushicore.tools.documentation.tooling_bridge import load, missing  # noqa: E402

K_BACKLOG = Path("docs/backlog")


@dataclass(frozen=True, slots=True)
class Repository:
    """Holds the root of one repository whose backlog is checked."""

    root: Path

    def has_backlog(self) -> bool:
        """Returns whether the repository holds a store to check."""
        return (self.root / K_BACKLOG).is_dir()


def collect(paths: list[Path]) -> Iterable[Repository]:
    """Returns each given folder that holds a docs/ tree."""
    return [Repository(path) for path in paths if (path / "docs").is_dir()]


def rule_backlog(repository: Repository,
                 load_module: Callable[[str, Path], ModuleType | None] = load) -> Iterator[Issue]:
    """Yields each fault `backlog check` finds, or one issue when the tooling package cannot be loaded.

    *load_module* loads a module of the tooling package by name and root; it defaults to the bridge.
    """
    if not repository.has_backlog():
        return
    backlog = load_module("backlog", repository.root)
    if backlog is None:
        yield missing(repository.root / "docs", "backlog")
        return
    store = backlog.BacklogStore(repository.root)
    for fault in backlog.check_backlog(store):
        yield Issue(fault.path, fault.line, fault.message)


K_CHECKER = Checker(
    description="Checks the backlog and the known issues in docs/backlog/ through the tooling package.",
    collect=collect,
    rules={"rule_backlog": rule_backlog},
)

if __name__ == "__main__":
    sys.exit(run(K_CHECKER))
