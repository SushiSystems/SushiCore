# toolkit_vendor_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""A toolkit vendor that publishes fixed releases and installs them in memory."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping

from .gpu_hardware import GpuHardware
from .toolkit_vendor import ToolkitSourceError


class FixedHardware:
    """Cards named by one text, which is also their fingerprint.

    Args:
        cards: The text that names the cards.
    """

    def __init__(self, cards: str) -> None:
        """Store the cards."""
        self.cards = cards

    def fingerprint(self) -> str:
        """Return the cards."""
        return self.cards

    def describe(self) -> str:
        """Return the cards."""
        return self.cards


class InMemoryToolkitVendor:
    """Answers the vendor questions from fixed tables and touches no disk or network.

    Args:
        base: The folder the releases would live in; it is only named, never created.
        labels: The release each hardware fingerprint needs; a fingerprint left out fits none.
        published: The releases an override may name.
        toolkit_roots: Folders that already hold a usable toolkit.
        system_toolkit: What ``find_system_toolkit`` returns.
        hardware: What ``query_hardware`` returns; ``None`` stands for a machine without a driver.
        name: The toolkit name for console lines.
        root_variable: The variable that names the toolkit root.
        override_variable: The variable that names a release.
        platform_key: The platform key of the vendor's index.

    Attributes:
        offline: Whether the index is unreachable; every call that reads it raises.
        chosen: The fingerprint of each hardware ``choose`` was asked about.
        installed: The label of each release ``install`` put in place.
        discards: How many times ``discard_downloads`` was called.
    """

    def __init__(self, base: Path, *, labels: Mapping[str, str] | None = None,
                 published: Iterable[str] = (), toolkit_roots: Iterable[Path] = (),
                 system_toolkit: Path | None = None, hardware: GpuHardware | None = None,
                 name: str = "Fake", root_variable: str = "FAKE_TOOLKIT_PATH",
                 override_variable: str = "FAKE_TOOLKIT_RELEASE",
                 platform_key: str = "linux-x86_64") -> None:
        """Start online, with nothing installed."""
        self.name = name
        self.root_variable = root_variable
        self.override_variable = override_variable
        self.platform_key = platform_key
        self.hardware = hardware
        self.offline = False
        self.chosen: list[str] = []
        self.installed: list[str] = []
        self.discards = 0
        self._base = base
        self._labels = dict(labels or {})
        self._published = tuple(published)
        self._roots = set(toolkit_roots)
        self._system = system_toolkit

    @property
    def toolkits_dir(self) -> Path:
        """Return the base folder."""
        return self._base

    def query_hardware(self) -> GpuHardware | None:
        """Return the fixed hardware."""
        return self.hardware

    def choose(self, hardware: GpuHardware) -> str | None:
        """Return the release the hardware's fingerprint maps to, or raise when offline."""
        self._reach_index()
        self.chosen.append(hardware.fingerprint())
        return self._labels.get(hardware.fingerprint())

    def resolve_override(self, text: str) -> str:
        """Return *text* when it is a published release, else raise."""
        self._reach_index()
        if text not in self._published:
            raise ToolkitSourceError(f"no release {text}")
        return text

    def is_installed(self, label: str) -> bool:
        """Report whether the release was installed."""
        return self.root_of(label) in self._roots

    def root_of(self, label: str) -> Path:
        """Return the release folder under the base."""
        return self._base / label

    def install(self, label: str) -> Path:
        """Mark the release as installed, or raise when offline."""
        self._reach_index()
        self._roots.add(self.root_of(label))
        self.installed.append(label)
        return self.root_of(label)

    def discard_downloads(self) -> None:
        """Count the call; there are no downloads."""
        self.discards += 1

    def is_toolkit_root(self, root: Path) -> bool:
        """Report whether *root* holds an installed or preset toolkit."""
        return root in self._roots

    def find_system_toolkit(self) -> Path | None:
        """Return the fixed system toolkit."""
        return self._system

    def _reach_index(self) -> None:
        """Fail as an unreachable index does."""
        if self.offline:
            raise ToolkitSourceError("offline")
