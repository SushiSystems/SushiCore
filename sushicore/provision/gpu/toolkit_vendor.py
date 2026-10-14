# toolkit_vendor.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""What one GPU vendor answers so that a toolkit release can be chosen from the hardware.

The reasoning is in docs/design/GPU_TOOLKIT_SELECTION.md.
"""

from __future__ import annotations

import typing
from pathlib import Path

from .gpu_hardware import GpuHardware


class ToolkitSourceError(Exception):
    """A vendor's release index or archive could not be read, verified or unpacked."""


@typing.runtime_checkable
class ToolkitVendor(typing.Protocol):
    """Chooses, installs and recognises one vendor's toolkit releases.

    A release is named by a label the vendor alone interprets, such as ``13.1.2``.
    """

    @property
    def name(self) -> str:
        """Return the toolkit's name for console lines, such as ``CUDA``."""
        ...

    @property
    def root_variable(self) -> str:
        """Return the variable consumers read the root from, such as ``CUDA_PATH``."""
        ...

    @property
    def override_variable(self) -> str:
        """Return the variable that names a release in place of the choice."""
        ...

    @property
    def platform_key(self) -> str:
        """Return the key of this platform in the vendor's index."""
        ...

    @property
    def toolkits_dir(self) -> Path:
        """Return the folder the vendor's releases and its choice file live in."""
        ...

    def query_hardware(self) -> GpuHardware | None:
        """Return the cards, or None when there is no driver to ask."""
        ...

    def choose(self, hardware: GpuHardware) -> str | None:
        """Return the label of the release the hardware needs, or None when none fits.

        Raises:
            ToolkitSourceError: The index could not be read.
        """
        ...

    def resolve_override(self, text: str) -> str:
        """Return the label of the newest release *text* names or prefixes.

        Raises:
            ToolkitSourceError: No published release matches *text*.
        """
        ...

    def is_installed(self, label: str) -> bool:
        """Report whether the release is in place."""
        ...

    def root_of(self, label: str) -> Path:
        """Return where the release is, or would be, installed."""
        ...

    def install(self, label: str) -> Path:
        """Install the release unless it is in place, and return its root.

        Raises:
            ToolkitSourceError: The release could not be downloaded, verified or unpacked.
        """
        ...

    def discard_downloads(self) -> None:
        """Delete archives kept for releases that were probed but not installed."""
        ...

    def is_toolkit_root(self, root: Path) -> bool:
        """Report whether *root* holds a usable toolkit of this vendor."""
        ...

    def find_system_toolkit(self) -> Path | None:
        """Return the root of a toolkit installed outside the root variable, or None."""
        ...
