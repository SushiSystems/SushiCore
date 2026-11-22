# run_service.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What the shared ``run`` command hands a CLI's run service, and the call it makes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Optional, Protocol, final


@final
@dataclass(frozen=True)
class RunRequest:
    """One ``run`` the user asked for.

    Args:
        target: The program named, or None when none was.
        pick: True when ``--pick``, or its old spelling, was given.
        list_all: True when ``--all`` was given, so the pick lists every program.
        build: False when ``--no-build`` was given.
        arguments: The arguments after ``--``, which go to the program unchanged.
        extra: The value of each parameter the CLI added, by name.
        obj: The object the Typer context carries, ``ctx.obj``; None when the CLI sets none.
    """

    target: Optional[str] = None
    pick: bool = False
    list_all: bool = False
    build: bool = True
    arguments: tuple[str, ...] = ()
    extra: Mapping[str, object] = field(default_factory=dict)
    obj: object = None


class RunService(Protocol):
    """What finds and starts one built program of a CLI's repository."""

    def run(self, request: RunRequest) -> int:
        """Builds unless told not to, starts the program of *request* and returns its exit code."""
