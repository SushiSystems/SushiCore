# cuda_selection.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Chooses the CUDA release a machine gets: the newest one its driver runs whose compiler
builds for every card in it.

NVIDIA removes architectures from the compiler only in a major release, so the newest release
of each major speaks for the whole major. Walking majors newest first therefore asks at most
one compiler per major, and a Pascal card stops the walk at 12.x on its own.
"""

from __future__ import annotations

import itertools
import typing

from .cuda_hardware import NvidiaHardware
from .cuda_release import Version

#: Returns the architectures the compiler of a release builds for, such as ``{"75", "89"}``.
ArchitectureProbe = typing.Callable[[Version], frozenset[str]]


def select_release(hardware: NvidiaHardware, versions: typing.Iterable[Version],
                   supported_architectures: ArchitectureProbe) -> Version | None:
    """Return the release to install, or None when no published release fits.

    Args:
        hardware: The cards and the driver's CUDA ceiling.
        versions: The published releases, in any order.
        supported_architectures: Asks one release's compiler which architectures it builds.
    """
    runnable = sorted((v for v in versions if v[:2] <= hardware.driver_cuda), reverse=True)
    needed = frozenset(hardware.architectures)
    for _major, releases in itertools.groupby(runnable, key=lambda v: v[0]):
        newest = next(releases)
        if needed <= supported_architectures(newest):
            return newest
    return None
