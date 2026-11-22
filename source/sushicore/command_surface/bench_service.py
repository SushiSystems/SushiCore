# bench_service.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What the shared ``bench`` command hands a CLI's benchmark service, and the call it makes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Protocol, final


@final
@dataclass(frozen=True)
class BenchRequest:
    """One ``bench`` the user asked for.

    Args:
        build_type: The ``--type`` value, one of the build types the CLI benchmarks.
        extra: The value of each parameter the CLI added, by name.
        obj: The object the Typer context carries, ``ctx.obj``; None when the CLI sets none.
    """

    build_type: str
    extra: Mapping[str, object] = field(default_factory=dict)
    obj: object = None


class BenchService(Protocol):
    """What runs the built benchmark programs of a CLI's repository."""

    def bench(self, request: BenchRequest) -> int:
        """Runs the benchmarks of *request* and returns the exit code."""
