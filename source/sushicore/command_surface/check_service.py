# check_service.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What the shared ``check`` command hands a CLI's check service, and the call it makes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Optional, Protocol, final


@final
@dataclass(frozen=True)
class CheckRequest:
    """One ``check`` the user asked for.

    Args:
        report: True when ``--report`` was given: count the findings and do not fail.
        rule: The one rule ``--rule`` names, or None for every rule.
        extra: The value of each parameter the CLI added, by name.
        obj: The object the Typer context carries, ``ctx.obj``; None when the CLI sets none.
    """

    report: bool = False
    rule: Optional[str] = None
    extra: Mapping[str, object] = field(default_factory=dict)
    obj: object = None


class CheckService(Protocol):
    """What runs the checkers of a CLI's repository."""

    def check(self, request: CheckRequest) -> int:
        """Runs the checkers *request* selects and returns the exit code."""
