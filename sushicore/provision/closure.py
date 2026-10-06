# closure.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Collects the fragments one module needs: its own and every module's it builds on."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Sequence

from sushicore import deps_fragment

#: Path of a module's fragment, relative to its checkout.
DEFAULT_FRAGMENT = "cli/sushistack.deps.toml"

#: Finds the checkout of the module a fragment names, or None when there is none.
Locate = Callable[[str], Optional[Path]]


@dataclass(frozen=True)
class Closure:
    """The fragments to read, dependencies first, and the modules with no checkout."""

    sources: tuple[tuple[Path, str], ...]
    missing: tuple[tuple[str, str], ...]


def resolve(key: str, root: Path, locate: Locate, *, fragment: str = DEFAULT_FRAGMENT,
            shared: Sequence[tuple[Path, str]] = ()) -> Closure:
    """Return the closure of the module *key* checked out at *root*.

    Args:
        key: The module's lower-cased name.
        root: The module's checkout.
        locate: Finds the checkout of a module named in ``depends_on``.
        fragment: The module's own fragment, relative to *root*.
        shared: Fragments placed before every module's.

    Raises:
        ValueError: The modules depend on one another in a cycle.
    """
    sources: list[tuple[Path, str]] = list(shared)
    missing: list[tuple[str, str]] = []
    done: set[str] = set()

    def visit(name: str, checkout: Path, relative: str, trail: tuple[str, ...]) -> None:
        """Append *name*'s dependencies, then *name*, to the closure."""
        if name in trail:
            raise ValueError(
                "Modules depend on one another in a cycle: " + " -> ".join((*trail, name)))
        if name in done:
            return
        done.add(name)
        path = checkout / relative
        if not path.is_file():
            return
        for dependency in deps_fragment.read(path).depends_on:
            found = locate(dependency)
            if found is None:
                if (dependency, name) not in missing:
                    missing.append((dependency, name))
                continue
            visit(dependency, found, DEFAULT_FRAGMENT, (*trail, name))
        sources.append((path, name))

    visit(key, root, fragment, ())
    return Closure(tuple(sources), tuple(missing))
