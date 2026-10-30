# module_provision.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""What one module CLI hands the shared provisioning commands."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from ..profile import ModuleProfile
from .closure import Locate
from .config import ProvisionConfig
from .doctor import Check
from .git_client import GitClient, IGitClient


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
