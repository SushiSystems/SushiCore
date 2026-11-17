# sushi_setup.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Prepares a module's pinned Sushi libraries before setup reads its closure."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, Sequence

from sushicore.deps_fragment import SushiPin

from . import home
from .closure import Locate
from .git_client import IGitClient
from .lock import LockTimeout, ProvisionLock
from .pin_chain import PinWalk, walk
from .pipeline import InstallContext, InstallPipeline
from .sushi_fetch import FetchSushiSourcesStep
from .sushi_sources import resolve


def locator(base: Locate, root: Path, pins: Sequence[SushiPin]) -> Locate:
    """Return *base*, falling back to the directory, sibling or fetched copy of a library.

    An unpinned library is looked for through its directory and its sibling only.
    """
    versions = {pin.name: pin.version for pin in pins}

    def locate(name: str) -> Optional[Path]:
        """Find *name* through *base* first, then through the resolution order."""
        found = base(name)
        if found is not None:
            return found
        resolved = resolve(root, name, versions.get(name, ""))
        return resolved.path if resolved is not None else None
    return locate


def _walk(owner: str, root: Path, pins: Sequence[SushiPin], console: Any) -> PinWalk | None:
    """Return the chain's walk; print each conflict or bad fragment on *console*, else None."""
    try:
        found = walk(owner, root, pins)
    except ValueError as exc:
        console.error(str(exc))
        return None
    for conflict in found.conflicts:
        console.error(conflict.message())
    return None if found.conflicts else found


def _fetch(ctx: InstallContext, root: Path, pins: Sequence[SushiPin], git: IGitClient,
           timeout: float, console: Any) -> bool:
    """Clone each of *pins* that no directory or sibling provides, under the root's lock."""
    pipeline = InstallPipeline([FetchSushiSourcesStep(root, pins, git, console)], console)
    try:
        with ProvisionLock(home.root() / ".lock", timeout=timeout):
            return pipeline.run(ctx, show_progress=False)
    except LockTimeout as exc:
        console.error(str(exc))
        return False


def prepare(ctx: InstallContext, root: Path, pins: Sequence[SushiPin], git: IGitClient,
            timeout: float, console: Any) -> bool:
    """Fetch every pinned library of the chain, one layer at a time; report success.

    Each round walks the pins of the libraries on disk, fetches what is missing, and walks
    again, because a library just fetched can pin another. It ends when a round adds no library.

    Args:
        ctx: The run's context; ``ctx.consumer`` names the module at *root*.
        root: The module's checkout.
        pins: The pins of its own fragment.
        git: Clones and inspects the libraries.
        timeout: Seconds to wait for another process's lock.
        console: The console the run prints through.
    """
    if not pins:
        return True
    known: set[str] = set()
    while True:
        found = _walk(ctx.consumer, root, pins, console)
        if found is None:
            return False
        names = {pin.name for pin in found.pins}
        if names == known:
            return True
        known = names
        if not _fetch(ctx, root, found.pins, git, timeout, console):
            return False
