# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The GPU backend contract: what a locator answers, what a spec declares."""

from __future__ import annotations

import dataclasses
import pathlib
import typing

from .._output import console

if typing.TYPE_CHECKING:
    from ..config import ProvisionConfig


@dataclasses.dataclass(frozen=True)
class ToolkitInstall:
    """The result of locating a vendor's GPU toolkit on the machine.

    Args:
        root: Install root of the toolkit.
        version: The toolkit's version string, when known.
    """

    root: pathlib.Path
    version: str | None


@typing.runtime_checkable
class ToolkitLocator(typing.Protocol):
    """Finds and, when possible, provisions one vendor's toolkit."""

    def locate(self, cfg: "ProvisionConfig") -> ToolkitInstall | None:
        """Return the toolkit install found on this machine, or None."""
        ...

    def provision(self, cfg: "ProvisionConfig", dry_run: bool) -> bool:
        """Install or report on the toolkit. Return True unless it failed fatally."""
        ...


class NotProvided:
    """A locator for a backend that has no answer on the current platform.

    Args:
        backend: The backend's vendor name, for the console message.
        platform: The platform name, for the console message.
    """

    def __init__(self, backend: str, platform: str) -> None:
        """Store the backend and platform names used in the report message."""
        self._backend = backend
        self._platform = platform

    def locate(self, cfg: "ProvisionConfig") -> ToolkitInstall | None:
        """Return None; this backend is never found on this platform."""
        return None

    def provision(self, cfg: "ProvisionConfig", dry_run: bool) -> bool:
        """Report that the backend is not provided here. Always succeeds."""
        console.info(f"{self._backend} is not provided on {self._platform}.")
        return True


class PlatformLocator:
    """Dispatches to a per-platform locator, falling back to :class:`NotProvided`.

    Args:
        backend: The backend's vendor name, used to build the fallback.
        locators: Platform name to locator, keyed by ``cfg.platform``'s values
            (``"windows"``, ``"linux"``, ``"darwin"``); an absent key falls back to
            :class:`NotProvided`.
    """

    def __init__(self, backend: str, locators: dict[str, ToolkitLocator]) -> None:
        """Store the backend name and the per-platform locator map."""
        self._backend = backend
        self._locators = dict(locators)

    def _for(self, cfg: "ProvisionConfig") -> ToolkitLocator:
        """Return the locator for cfg's platform, or a NotProvided fallback."""
        platform = getattr(cfg, "platform", None)
        found = self._locators.get(platform)
        if found is not None:
            return found
        return NotProvided(self._backend, str(platform))

    def locate(self, cfg: "ProvisionConfig") -> ToolkitInstall | None:
        """Locate through the locator registered for cfg's platform."""
        return self._for(cfg).locate(cfg)

    def provision(self, cfg: "ProvisionConfig", dry_run: bool) -> bool:
        """Provision through the locator registered for cfg's platform."""
        return self._for(cfg).provision(cfg, dry_run)


@dataclasses.dataclass(frozen=True)
class GpuBackendSpec:
    """One vendor's complete answer to the GPU backend contract.

    Args:
        vendor: The backend's own name, e.g. ``"cuda"``.
        probe_vendor: The vendor key ``probe.py`` reports, e.g. ``"nvidia"``.
        locator: Finds and provisions the toolkit for this vendor.
        adapter_option: The Unified Runtime CMake option that builds this adapter.
        adapter_definitions: Builds the extra configure definitions from a
            located toolkit, naming its root to the adapter build.
        adapter_target: The CMake build target that produces the adapter.
        adapter_binaries: Base names of the binaries the adapter build
            produces, without platform prefix or suffix. The adapter builder maps
            each name to its platform file name: ``<name>.dll`` on Windows,
            ``lib<name>.so*`` on Linux.
    """

    vendor: str
    probe_vendor: str
    locator: ToolkitLocator
    adapter_option: str
    adapter_definitions: typing.Callable[[ToolkitInstall], dict[str, str]]
    adapter_target: str
    adapter_binaries: tuple[str, ...]
