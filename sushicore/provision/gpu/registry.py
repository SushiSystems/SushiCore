# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The ordered set of declared GPU backends and lookups over it."""

from __future__ import annotations

from .backend import GpuBackendSpec
from .cuda import CUDA
from .level_zero import LEVEL_ZERO
from .rocm import ROCM


class Registry:
    """An ordered, duplicate-free set of :class:`GpuBackendSpec`.

    :param specs: The backends to register, in report order.
    :raises ValueError: When two specs share a vendor name or a probe key.
    """

    def __init__(self, specs: tuple[GpuBackendSpec, ...]) -> None:
        """Validate and store *specs*, indexing them by vendor and probe key."""
        by_vendor: dict[str, GpuBackendSpec] = {}
        by_probe: dict[str, GpuBackendSpec] = {}
        for spec in specs:
            if spec.vendor in by_vendor:
                raise ValueError(f"Duplicate GPU backend vendor: '{spec.vendor}'")
            if spec.probe_vendor in by_probe:
                raise ValueError(f"Duplicate GPU backend probe vendor: '{spec.probe_vendor}'")
            by_vendor[spec.vendor] = spec
            by_probe[spec.probe_vendor] = spec
        self._specs = tuple(specs)
        self._by_vendor = by_vendor
        self._by_probe = by_probe

    def all(self) -> tuple[GpuBackendSpec, ...]:
        """Return every registered backend, in report order."""
        return self._specs

    def for_probe_vendor(self, key: str) -> GpuBackendSpec | None:
        """Return the backend whose probe key is *key*, or None."""
        return self._by_probe.get(key)

    def for_vendor(self, name: str) -> GpuBackendSpec | None:
        """Return the backend whose own vendor name is *name*, or None."""
        return self._by_vendor.get(name)


BACKENDS: tuple[GpuBackendSpec, ...] = (CUDA, ROCM, LEVEL_ZERO)

DEFAULT_REGISTRY = Registry(BACKENDS)
