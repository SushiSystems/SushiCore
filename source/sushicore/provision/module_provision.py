# module_provision.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What one module CLI hands the shared provisioning commands."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional

from ..profile import ModuleProfile
from .closure import Locate
from .config import ProvisionConfig
from .doctor import Check
from .git_client import GitClient, IGitClient

if TYPE_CHECKING:
    from .packages import IPackageManager
    from .steps import MachineActions


def _locate_nothing(name: str) -> Optional[Path]:
    """Report that the module *name* has no checkout."""
    del name
    return None


@dataclass(frozen=True)
class ModuleProvision:
    """What one module CLI hands the shared commands.

    Args:
        locate: Finds the checkout of a module the fragment's ``depends_on`` names.
        panel: The help panel the commands are listed under, or None for the default.
        is_binary: Reports a binary install, which registers ``doctor`` alone.
        uses_base: Whether the shared base fragment joins the module's own.
        git: Builds the git client that fetches and inspects pinned Sushi libraries.
        fragment: The dependency fragment below the project root; None reads the module's manifest.
        config_dir: The folder below the project root that holds the local configuration and the
            workspace link.
        groups: Check groups beyond the stock ones that this module's extra checks belong to; they
            join the groups ``doctor --for`` accepts and lists.
        managers: Builds the package managers a configuration provisions through; None builds the
            platform's own.
        base_checks: Builds the stock checks ``doctor`` opens with from a configuration and the
            fix text; None uses the standard ones.
        toolchains: Reads ``(name, present, detail)`` for each SYCL toolchain off the machine for a
            configuration and the GPU flag; None probes the machine.
        actions: The calls the setup steps make that reach the machine; None makes the real ones.
        register: Records the module in a workspace as ``(workspace, key, root)``; None writes the
            workspace's registry file.
        lock_timeout: Seconds ``setup`` waits for the provision lock and for a pinned module's fetch
            lock; None waits the stock ten minutes.
    """

    profile: ModuleProfile
    project_root: Callable[[], Path]
    load_config: Callable[[], ProvisionConfig]
    console: Callable[[], object]
    extra_checks: Callable[[], list[Check]] = lambda: []
    fragment: Optional[str] = None
    locate: Locate = _locate_nothing
    panel: Optional[str] = None
    is_binary: Callable[[], bool] = lambda: False
    uses_base: bool = False
    git: Callable[[], IGitClient] = GitClient
    config_dir: str = "cli"
    groups: tuple[str, ...] = ()
    managers: Optional[Callable[[ProvisionConfig], "list[IPackageManager]"]] = None
    base_checks: Optional[Callable[[ProvisionConfig, str], list[Check]]] = None
    toolchains: Optional[Callable[[ProvisionConfig, bool], list[tuple[str, bool, str]]]] = None
    actions: Optional["MachineActions"] = None
    lock_timeout: Optional[float] = None
    register: Optional[Callable[[Path, str, Path], None]] = None
