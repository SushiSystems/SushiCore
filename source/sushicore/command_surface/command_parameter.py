# command_parameter.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Declares one parameter of a canonical command: its name, its type and its Typer default."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, final


@final
@dataclass(frozen=True)
class CommandParameter:
    """One option or argument of a command, as a Typer function parameter declares it.

    Args:
        name: The Python name of the parameter; the service reads its value under this name.
        annotation: The type Typer parses the value into, such as ``bool`` or ``Optional[int]``.
        default: The ``typer.Option(...)`` or ``typer.Argument(...)`` that names its flags.
    """

    name: str
    annotation: Any
    default: Any
