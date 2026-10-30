# module_plan.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Works out what a module needs: its package managers, its fragments and its dependency source."""

from __future__ import annotations

from pathlib import Path

from ..deps_fragment import pins_at
from . import closure as closure_module
from . import manifests, sushi_setup
from .closure import Closure
from .config import ProvisionConfig
from .fragments import TomlDependencySource
from .module_provision import ModuleProvision
from .packages import (
    AptManager,
    DirectDownloadWindowsManager,
    DnfManager,
    IPackageManager,
    PacmanManager,
    VcpkgManager,
    WingetManager,
    YumManager,
    ZypperManager,
)


def managers_for(cfg: ProvisionConfig) -> list[IPackageManager]:
    """Returns the package managers this platform provisions dependencies through."""
    if cfg.is_windows:
        return [WingetManager(), DirectDownloadWindowsManager(), VcpkgManager(cfg)]
    return [AptManager(), DnfManager(), YumManager(), PacmanManager(), ZypperManager(),
            VcpkgManager(cfg)]


def closure_for(module: ModuleProvision, root: Path) -> Closure:
    """Returns the fragments *module* needs: the base when asked for, its modules', its own.

    Raises:
        ValueError: The modules depend on one another in a cycle, or a fragment is malformed.
    """
    shared = [(manifests.base_fragment(), manifests.BASE_OWNER)] if module.uses_base else []
    locate = sushi_setup.locator(module.locate, root, pins_at(root / module.fragment))
    return closure_module.resolve(module.profile.key, root, locate,
                                  fragment=module.fragment, shared=shared)


def source_for(module: ModuleProvision, root: Path, found: Closure) -> TomlDependencySource:
    """Returns the dependency source over *found*, or over the module's own fragment path."""
    sources = list(found.sources) or [(root / module.fragment, module.profile.key)]
    return TomlDependencySource(sources)


def missing_module_message(module: str, wanted_by: str) -> str:
    """Returns the line that tells a user where the checkout of *module* belongs."""
    return (f"{wanted_by} builds on {module}, and no checkout of it was found. "
            f"Clone it beside this repository or set {module.upper()}_DIR.")
