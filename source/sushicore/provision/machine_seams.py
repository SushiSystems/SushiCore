# machine_seams.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The three builders a module CLI replaces to make provisioning read a machine it does not run on."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Optional

from .config import ProvisionConfig
from .doctor import Check

if TYPE_CHECKING:
    from .packages import IPackageManager


@dataclass(frozen=True, slots=True)
class MachineSeams:
    """What a module hands the shared commands in place of the real machine reads.

    Args:
        managers: Builds the package managers a configuration provisions through; None builds the
            platform's own.
        base_checks: Builds the stock checks ``doctor`` opens with from a configuration and the
            fix text; None uses the standard ones.
        toolchains: Reads ``(name, present, detail)`` for each SYCL toolchain off the machine for a
            configuration and the GPU flag; None probes the machine.
    """

    managers: Optional[Callable[[ProvisionConfig], "list[IPackageManager]"]] = None
    base_checks: Optional[Callable[[ProvisionConfig, str], list[Check]]] = None
    toolchains: Optional[Callable[[ProvisionConfig, bool], list[tuple[str, bool, str]]]] = None
