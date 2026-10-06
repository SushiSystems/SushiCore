# model.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The data a help screen is drawn from."""

from __future__ import annotations

from dataclasses import dataclass
from typing import final


@final
@dataclass(frozen=True, slots=True)
class HelpSection:
    """Holds a heading and the term and text pairs listed under it."""

    heading: str
    entries: tuple[tuple[str, str], ...]


@final
@dataclass(frozen=True, slots=True)
class HelpModel:
    """Holds everything one help screen shows."""

    name: str
    description: str
    usage: str
    is_root: bool
    commands: tuple[HelpSection, ...]
    arguments: tuple[tuple[str, str], ...]
    options: tuple[tuple[str, str], ...]
    examples: tuple[tuple[str, str], ...]
