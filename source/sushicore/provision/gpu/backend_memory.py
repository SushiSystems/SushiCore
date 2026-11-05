# backend_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""A toolkit locator that answers a fixed install and records its calls, touching no machine."""

from __future__ import annotations

import typing

from .backend import ToolkitInstall

if typing.TYPE_CHECKING:
    from ..config import ProvisionConfig


class InMemoryToolkitLocator:
    """Locates a fixed toolkit, provisions with a fixed outcome and records every call.

    Args:
        install: What ``locate`` returns; ``None`` stands for a toolkit that is not installed.
        provisioned: What ``provision`` returns.
    """

    def __init__(self, install: ToolkitInstall | None = None, *,
                 provisioned: bool = True) -> None:
        """Start with no recorded calls."""
        self._install = install
        self._provisioned = provisioned
        self.located: list["ProvisionConfig"] = []
        self.provisioned_with: list[tuple["ProvisionConfig", bool]] = []

    def locate(self, cfg: "ProvisionConfig") -> ToolkitInstall | None:
        """Record *cfg* and return the fixed install."""
        self.located.append(cfg)
        return self._install

    def provision(self, cfg: "ProvisionConfig", dry_run: bool) -> bool:
        """Record *cfg* and *dry_run*, change nothing and return the fixed outcome."""
        self.provisioned_with.append((cfg, dry_run))
        return self._provisioned
