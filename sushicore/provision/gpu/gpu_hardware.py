# gpu_hardware.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The cards of one vendor, as far as choosing a toolkit release needs to know them."""

from __future__ import annotations

import typing


@typing.runtime_checkable
class GpuHardware(typing.Protocol):
    """The cards of one vendor in a machine, as its driver reports them."""

    def fingerprint(self) -> str:
        """Return a stable text that changes when the cards or the driver do."""
        ...

    def describe(self) -> str:
        """Return the cards for a console line, such as ``sm_61, sm_89``."""
        ...
