# gpu_stack.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Dispatches GPU stack provisioning to the registered backend for one vendor."""

from __future__ import annotations

import typing
from typing import Any

from ..default_console import console_or_default
from ..gpu.registry import DEFAULT_REGISTRY, Registry

if typing.TYPE_CHECKING:
    from ..config import ProvisionConfig


def install_gpu_stack(cfg: "ProvisionConfig", vendor: str, dry_run: bool,
                      registry: Registry | None = None, *, console: Any = None) -> bool:
    """Provision *vendor*'s compute SDK through its registered backend spec.

    Args:
        registry: The backend registry to ask; the stock one when ``None``.
        console: The console the provisioning prints through.
    """
    console = console_or_default(console, "install_gpu_stack")
    spec = (registry or DEFAULT_REGISTRY).for_probe_vendor(vendor)
    if spec is None:
        console.info("No discrete GPU detected; using the CPU (SPIR/OpenCL) path only.")
        return True
    return spec.locator.provision(cfg, dry_run, console)
