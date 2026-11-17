# adapter_provisioner.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The call that builds the adapters of one toolchain."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from .config import ProvisionConfig
from .provision_console import ProvisionConsole

if TYPE_CHECKING:
    from .gpu.adapter_builder import AdapterBuilder
    from .gpu.registry import Registry


class AdapterProvisioner(Protocol):
    """Builds every located backend's adapter for one toolchain tree."""

    def __call__(self, cfg: ProvisionConfig, registry: Registry, toolchain_root: Path,
                 builder: AdapterBuilder, dry_run: bool, *, console: ProvisionConsole) -> None:
        """Build the adapters of the backends *registry* locates under *toolchain_root*."""
        ...
