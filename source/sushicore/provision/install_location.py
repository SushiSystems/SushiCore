# install_location.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The part of the toolkit contract the GPU backends and the SYCL toolchains share."""

from __future__ import annotations

import dataclasses
import pathlib
import typing

if typing.TYPE_CHECKING:
    from .config import ProvisionConfig


@typing.final
@dataclasses.dataclass(frozen=True)
class ToolkitInstall:
    """The result of locating a toolkit or toolchain on the machine.

    Args:
        root: Install root of the toolkit.
        version: The toolkit's version string, when known.
    """

    root: pathlib.Path
    version: str | None


@typing.runtime_checkable
class ToolkitFinder(typing.Protocol):
    """Finds one toolkit or toolchain on this machine."""

    def locate(self, cfg: "ProvisionConfig") -> ToolkitInstall | None:
        """Return the install found on this machine, or None."""
        ...
