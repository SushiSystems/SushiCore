# sushi_source_check.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The doctor checks of pinned Sushi libraries: where each came from, and pins that conflict."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from sushicore.deps_fragment import SushiPin

from .doctor import CheckResult, FunctionCheck, State
from .git_client import IGitClient
from .pin_chain import conflicts
from .sushi_sources import SourceKind, resolve


def sushi_source_check(root: Path, pin: SushiPin, git: IGitClient, fix: str) -> FunctionCheck:
    """Return a check reporting which source holds *pin*, warning on a sibling off the pin.

    Args:
        root: The checkout of the module that links the library.
        pin: The library's pin.
        git: Reads a checkout's HEAD.
        fix: The command that fetches a missing library.
    """
    def fn() -> CheckResult:
        """Resolve the library and compare a sibling's HEAD with the pin."""
        found = resolve(root, pin.name, pin.version)
        if found is None:
            return CheckResult(State.FAIL, f"{pin.name} {pin.version}: no checkout found", fix)
        detail = f"{found.kind.value} {found.path}"
        if found.kind is SourceKind.SIBLING:
            head = git.head(found.path)
            if head != pin.commit:
                return CheckResult(State.WARN,
                                   f"{detail} is at {head or '(unknown)'}, pinned {pin.commit}",
                                   f"check out {pin.version} in {found.path}")
        return CheckResult(State.OK, detail)
    return FunctionCheck(f"sushi {pin.name}", "build", True, fn)


def pin_conflict_check(owner: str, root: Path, pins: Sequence[SushiPin]) -> FunctionCheck:
    """Return a check failing when the chain under *owner* pins one library at two versions.

    Args:
        owner: The name of the repository at *root*.
        root: Its checkout.
        pins: The pins of its own fragment.
    """
    def fn() -> CheckResult:
        """Walk the chain and name every conflict."""
        try:
            found = conflicts(owner, root, pins)
        except ValueError as exc:
            return CheckResult(State.FAIL, str(exc))
        if found:
            return CheckResult(State.FAIL, " ".join(c.message() for c in found),
                               "move the pins to one version")
        return CheckResult(State.OK, f"{len(pins)} pinned, no conflict")
    return FunctionCheck("sushi pins", "build", True, fn)


def unpinned_check(root: Path, name: str) -> FunctionCheck:
    """Return a row warning that *name* is in ``depends_on`` with no ``[sushi.<name>]`` pin.

    Args:
        root: The checkout of the module that builds on *name*.
        name: The unpinned module.
    """
    def fn() -> CheckResult:
        """Name where the unpinned module was found, if anywhere."""
        found = resolve(root, name)
        where = f"{found.kind.value} {found.path}" if found is not None else "no checkout found"
        return CheckResult(State.WARN, f"not pinned; pin it in [sushi.{name}] ({where})",
                           f"add [sushi.{name}] with version and commit")
    return FunctionCheck(f"sushi {name}", "build", False, fn)
