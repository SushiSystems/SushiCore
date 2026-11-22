# build_types.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Holds the build types one command takes with ``--type`` and the one it takes when none is given."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import final

from .errors import BuildTypeError


@final
@dataclass(frozen=True)
class BuildTypes:
    """The values of ``--type`` for one command.

    Args:
        names: The build types, such as ``("debug", "release", "relwithdebinfo")``.
        default: The type the command takes without ``--type``; one of *names*.

    Raises:
        BuildTypeError: *names* is empty, or *default* is not among them.
    """

    names: tuple[str, ...]
    default: str

    def __post_init__(self) -> None:
        """Refuses an empty set and a default outside it."""
        if not self.names:
            raise BuildTypeError("a command that takes --type needs at least one build type.")
        if self.default not in self.names:
            raise BuildTypeError(
                f"the default build type {self.default!r} is not one of {', '.join(self.names)}.")

    def choice(self) -> type[Enum]:
        """Returns a string enumeration of *names*, the type Typer offers as the choices."""
        return Enum("BuildType", [(name, name) for name in self.names], type=str)
