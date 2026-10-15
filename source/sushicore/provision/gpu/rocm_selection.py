# rocm_selection.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Chooses the ROCm tarball a machine gets: the newest release with one family that covers
every AMD card in it, and of those the family with the fewest cards beyond them."""

from __future__ import annotations

import typing

from .amd_hardware import AmdHardware
from .rocm_package import RocmPackage


def select_package(hardware: AmdHardware,
                   packages: typing.Iterable[RocmPackage]) -> RocmPackage | None:
    """Return the tarball to install, or None when no published family covers every card."""
    fitting = [p for p in packages if all(p.builds_for(t) for t in hardware.targets)]
    if not fitting:
        return None
    return max(fitting, key=lambda p: (p.version, p.specificity(), p.family == p.pattern,
                                       p.family.endswith("-all"), p.family))
