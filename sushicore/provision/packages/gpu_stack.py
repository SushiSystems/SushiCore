# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Dispatches GPU stack provisioning to the registered backend for one vendor."""

from __future__ import annotations

import typing

from .._output import console
from ..gpu.registry import DEFAULT_REGISTRY

if typing.TYPE_CHECKING:
    from ..config import ProvisionConfig


def install_gpu_stack(cfg: "ProvisionConfig", vendor: str, dry_run: bool) -> bool:
    """Provision *vendor*'s compute SDK through its registered backend spec."""
    spec = DEFAULT_REGISTRY.for_probe_vendor(vendor)
    if spec is None:
        console.info("No discrete GPU detected; using the CPU (SPIR/OpenCL) path only.")
        return True
    return spec.locator.provision(cfg, dry_run)
