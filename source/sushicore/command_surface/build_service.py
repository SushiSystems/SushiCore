# build_service.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What the shared ``build`` command hands a CLI's build service, and the call it makes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Optional, Protocol, final


@final
@dataclass(frozen=True)
class BuildRequest:
    """One ``build`` the user asked for.

    Args:
        build_type: The ``--type`` value, one of the CLI's build types.
        sanitizers: The ``--sanitize`` set in the order of ``K_SANITIZER_KINDS``; empty for none.
        defines: Each ``-D`` value, ``VAR=VALUE``, in the order given.
        jobs: The job count: ``--jobs``, else the ``build_jobs`` config key, else the default;
            the command always sets it, None only in a request made by hand.
        tests: False when ``--no-test`` was given.
        report: True when ``--report`` was given.
        extra: The value of each parameter the CLI added, by name.
        obj: The object the Typer context carries, ``ctx.obj``; None when the CLI sets none.
    """

    build_type: str
    sanitizers: tuple[str, ...] = ()
    defines: tuple[str, ...] = ()
    jobs: Optional[int] = None
    tests: bool = True
    report: bool = False
    extra: Mapping[str, object] = field(default_factory=dict)
    obj: object = None


class BuildService(Protocol):
    """What configures and builds one tree of a CLI's repository."""

    def build(self, request: BuildRequest) -> int:
        """Configures when needed, builds the tree of *request* and returns the exit code."""
