# bench_command.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Registers the shared ``bench`` command; the CLI hands it the service that runs its benchmarks."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Mapping, Sequence

from .bench_service import BenchRequest, BenchService
from .build_types import BuildTypes
from .command_function import command_function
from .command_parameter import CommandParameter
from .options import type_option
from .panels import K_RUN_PANEL
from .verbs import K_BENCH

if TYPE_CHECKING:
    import typer

K_BENCH_SUMMARY = "Run the built benchmark programs. A benchmark measures; it does not pass or fail."


def register_bench_command(
    app: "typer.Typer", service: BenchService, *, program: str, build_types: BuildTypes,
    panel: str = K_RUN_PANEL, parameters: Sequence[CommandParameter] = (),
    examples: Sequence[str] = (),
) -> None:
    """Add ``bench`` to *app*: ``--type``, whose default is the type a timing is taken on.

    Args:
        app: The CLI's Typer application.
        service: Runs the benchmarks a request names.
        program: The CLI's command, such as ``sd``, which the examples are written with.
        build_types: The values of ``--type`` and its default, usually ``release``.
        panel: The help panel the command is listed under.
        parameters: Options of the CLI's own, listed after the shared ones and handed over as ``extra``.
        examples: Example lines of the CLI's own, listed after the shared ones.
    """
    def act(ctx: Any, values: Mapping[str, Any], extra: Mapping[str, object]) -> int:
        """Builds the request from the parsed values and hands it to the service."""
        return service.bench(BenchRequest(
            build_type=values["build_type"].value, extra=extra, obj=ctx.obj))

    shared = (type_option(build_types, "Build type of the benchmark programs"),)
    epilog = "\n".join((
        f"{program} bench  # Every benchmark program, from the {build_types.default} tree",
        *examples,
    ))
    app.command(K_BENCH, rich_help_panel=panel, epilog=epilog)(
        command_function(shared, parameters, act, K_BENCH_SUMMARY))
