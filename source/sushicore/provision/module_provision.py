# module_provision.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What one module CLI hands the shared provisioning commands."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional, final

from ..profile import ModuleProfile
from .closure import Locate
from .config import ProvisionConfig
from .default_console import DEFAULT_CONSOLE
from .dependency_home import DEFAULT_HOME, DependencyHome
from .provision_console import ProvisionConsole
from .check import Check
from .git_client import GitClient, IGitClient
from .machine_seams import MachineSeams

if TYPE_CHECKING:
    from .machine_actions import MachineActions


def _locate_nothing(name: str) -> Optional[Path]:
    """Report that the module *name* has no checkout."""
    del name
    return None


@final
@dataclass(frozen=True)
class ModuleProvision:
    """What one module CLI hands the shared commands.

    Args:
        console: Returns the console the commands print through, called on each use.
        locate: Finds the checkout of a module the fragment's ``depends_on`` names.
        is_binary: Reports a binary install, which registers ``doctor`` alone.
        uses_base: Whether the shared base fragment joins the module's own.
        lock_timeout: Seconds ``setup`` waits for a lock; None waits ten minutes.
    """

    profile: ModuleProfile
    project_root: Callable[[], Path]
    load_config: Callable[[], ProvisionConfig]
    console: Callable[[], ProvisionConsole] = DEFAULT_CONSOLE
    extra_checks: Callable[[], list[Check]] = lambda: []
    fragment: Optional[str] = None
    locate: Locate = _locate_nothing
    panel: Optional[str] = None
    is_binary: Callable[[], bool] = lambda: False
    uses_base: bool = False
    git: Optional[Callable[[], IGitClient]] = None
    config_dir: str = "cli"
    groups: tuple[str, ...] = ()
    seams: MachineSeams = MachineSeams()
    actions: Optional["MachineActions"] = None
    lock_timeout: Optional[float] = None
    home: DependencyHome = DEFAULT_HOME
    register: Optional[Callable[[Path, str, Path], None]] = None

    def git_client(self) -> IGitClient:
        """Return the git client of this module: the one ``git`` builds, else the stock one."""
        if self.git is not None:
            return self.git()
        return GitClient(console=self.console())
