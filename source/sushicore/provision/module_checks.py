# module_checks.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Assembles the rows ``doctor`` runs for a source checkout of a module."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

from sushicore.deps_fragment import Fragment

from . import home, probe
from .checks import (
    capability_check,
    digest_check,
    fragment_check,
    modules_check,
    stamp_check,
    standard_checks,
)
from .config import ProvisionConfig
from .doctor import Check
from .fragments import IDependencySource
from .git_client import IGitClient
from .packages import IPackageManager
from .steps import held_by_managers
from .sushi_source_check import pin_conflict_check, sushi_source_check, unpinned_check


@dataclass(frozen=True)
class ModuleState:
    """What the doctor rows of one module read.

    Args:
        owner: The module's lower-case name.
        program: The command a user types, such as ``sr``.
        own: The module's own fragment, or None when it has none.
        missing: Each module with no checkout and the module that wanted it.
    """

    cfg: ProvisionConfig
    root: Path
    owner: str
    program: str
    own: Optional[Fragment]
    source: IDependencySource
    missing: Sequence[tuple[str, str]]


def _sushi_checks(state: ModuleState, git: IGitClient, fix: str) -> list[Check]:
    """Return one row per pinned or unpinned Sushi library, and the pin conflict row."""
    if state.own is None:
        return []
    pins = state.own.pins
    pinned = {pin.name for pin in pins}
    rows: list[Check] = [sushi_source_check(state.root, pin, git, fix) for pin in pins]
    rows += [unpinned_check(state.root, name) for name in state.own.depends_on
             if name not in pinned]
    if pins:
        rows.append(pin_conflict_check(state.owner, state.root, pins))
    return rows


def doctor_checks(state: ModuleState, managers: list[IPackageManager],
                  git: IGitClient) -> list[Check]:
    """Return every check ``doctor`` runs for *state*'s module, before its own extra checks."""
    cfg = state.cfg
    fix = f"{state.program} setup"
    clone = "clone it beside this repository"
    return (standard_checks(cfg, fix=fix)
            + [modules_check(state.missing, clone),
               capability_check(state.source, probe.toolchain_presence(cfg), fix),
               fragment_check(state.source, cfg.platform, False, fix,
                              held_by_managers(managers, cfg.platform)),
               stamp_check(home.root()),
               digest_check(state.source, cfg.platform)]
            + _sushi_checks(state, git, fix))
