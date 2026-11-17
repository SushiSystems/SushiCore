# toolchain.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The SYCL toolchain contract: what an installer answers, what a run hands it."""

from __future__ import annotations

import dataclasses
import typing
from typing import Any, Callable

from ..install_location import ToolkitFinder
from ..licence_consent import Licence
from ..packages import IPackageManager, LinuxPackageManager
from ..install_context import InstallContext


@dataclasses.dataclass(frozen=True, slots=True)
class ToolchainEnv:
    """What one install run hands every toolchain installer.

    Args:
        console: The console the installer prints through.
        managers: The package managers this run installs through.
        mgr: The Linux distro package manager; None on a target without one.
        vcpkg: The vcpkg manager, or None when unavailable.
        install_oneapi: Runs the oneAPI offline installer for a run and reports success.
    """

    console: Any
    managers: list[IPackageManager]
    mgr: LinuxPackageManager | None
    vcpkg: IPackageManager | None
    install_oneapi: Callable[[InstallContext], bool]


@typing.runtime_checkable
class Toolchain(ToolkitFinder, typing.Protocol):
    """Finds one SYCL toolchain, names its licences and installs it.

    Attributes:
        key: The toolchain's own name, e.g. ``"intel-llvm"``.
        selection_field: The :class:`ToolchainSelection` field that selects it.
    """

    key: str
    selection_field: str

    def licences(self, ctx: InstallContext) -> list[Licence]:
        """Return the licences installing this toolchain needs for *ctx*; empty when none."""
        ...

    def install(self, ctx: InstallContext, env: ToolchainEnv) -> bool:
        """Install the toolchain and record its paths in *ctx*. Return False on a fatal failure."""
        ...
