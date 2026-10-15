# toolkit_choice.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The toolkit release chosen for one machine's hardware, as it is recorded."""

from __future__ import annotations

import dataclasses
import typing


@typing.final
@dataclasses.dataclass(frozen=True, slots=True)
class ToolkitChoice:
    """One recorded choice.

    Args:
        fingerprint: :meth:`GpuHardware.fingerprint` of the hardware it was made for.
        platform: The redistributable platform key, such as ``linux-x86_64``.
        release: The chosen release, such as ``13.1.2``.
    """

    fingerprint: str
    platform: str
    release: str
