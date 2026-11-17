# gpu_machine.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The machine calls the GPU stage of an install run makes."""

from __future__ import annotations

from typing import Callable, Protocol

from .config import ProvisionConfig
from .dependency_home import DependencyHome


class ConfigResolver(Protocol):
    """Probes the machine-specific tool paths of a configuration."""

    def __call__(self, cfg: ProvisionConfig, gpu: bool = False,
                 home: DependencyHome | None = None) -> dict[str, str]:
        """Return the fields found for *cfg*; the GPU toolkits too when *gpu* is true.

        The roots of *home* are searched; the default home's when ``None``.
        """
        ...


class GpuMachine(Protocol):
    """What the GPU stage reads off the machine, replaceable by a test."""

    @property
    def refresh_path(self) -> Callable[[], None]:
        """Reloads ``PATH`` from the registry (Windows only)."""
        ...

    @property
    def resolve_config(self) -> ConfigResolver:
        """Probes the machine-specific tool paths of a configuration."""
        ...

    @property
    def detect_vendor(self) -> Callable[[], str]:
        """Reads the discrete-GPU vendor off the machine."""
        ...
