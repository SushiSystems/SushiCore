# sushi_setup.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Prepares a module's pinned Sushi libraries before setup reads its closure."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Sequence

from sushicore.deps_fragment import SushiPin

from . import home
from ._output import console
from .closure import Locate
from .git_client import IGitClient
from .lock import LockTimeout, ProvisionLock
from .pin_chain import conflicts
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


def _pins_agree(owner: str, root: Path, pins: Sequence[SushiPin]) -> bool:
    """Report whether the chain pins each library at one version; print each conflict."""
    try:
        found = conflicts(owner, root, pins)
    except ValueError as exc:
        console.error(str(exc))
        return False
    for conflict in found:
        console.error(conflict.message())
    return not found


def _fetch(ctx: InstallContext, root: Path, pins: Sequence[SushiPin], git: IGitClient,
           timeout: float) -> bool:
    """Clone each of *pins* that no directory or sibling provides, under the root's lock."""
    pipeline = InstallPipeline([FetchSushiSourcesStep(root, pins, git)])
    try:
        with ProvisionLock(home.root() / ".lock", timeout=timeout):
            return pipeline.run(ctx, show_progress=False)
    except LockTimeout as exc:
        console.error(str(exc))
        return False


def prepare(ctx: InstallContext, root: Path, pins: Sequence[SushiPin], git: IGitClient,
            timeout: float) -> bool:
    """Check the chain's pins, fetch what is missing, and check again; report success.

    The second check reads the fragments of the libraries just fetched.

    Args:
        ctx: The run's context; ``ctx.consumer`` names the module at *root*.
        root: The module's checkout.
        pins: The pins of its own fragment.
        git: Clones and inspects the libraries.
        timeout: Seconds to wait for another process's lock.
    """
    if not pins:
        return True
    if not _pins_agree(ctx.consumer, root, pins):
        return False
    if not _fetch(ctx, root, pins, git, timeout):
        return False
    return _pins_agree(ctx.consumer, root, pins)

