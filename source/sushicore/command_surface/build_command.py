# build_command.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Registers the shared ``build`` command; the CLI hands it the service that builds a tree."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Mapping, Sequence

from .build_service import BuildRequest, BuildService
from .build_types import BuildTypes
from .command_function import command_function
from .command_parameter import CommandParameter
from .options import define_option, jobs_option, no_test_option, report_option, type_option
from .panels import K_BUILD_PANEL
from .sanitize_option import K_SANITIZER_KINDS, parse_sanitizers, sanitize_option
from .verbs import K_BUILD

if TYPE_CHECKING:
    import typer

K_BUILD_SUMMARY = "Configure the tree of the build type when needed, then build it."


def register_build_command(
    app: "typer.Typer", service: BuildService, *, program: str, build_types: BuildTypes,
    panel: str = K_BUILD_PANEL, sanitizers: Sequence[str] = K_SANITIZER_KINDS,
    parameters: Sequence[CommandParameter] = (), examples: Sequence[str] = (),
) -> None:
    """Add ``build`` to *app*: ``--type``, ``--sanitize``, ``--define``, ``--jobs``, ``--no-test`` and ``--report``.

    Args:
        app: The CLI's Typer application.
        service: Builds the tree a request names.
        program: The CLI's command, such as ``sd``, which the examples are written with.
        build_types: The values of ``--type`` and its default.
        panel: The help panel the command is listed under.
        sanitizers: The sanitizers ``--sanitize`` takes; a subset of ``K_SANITIZER_KINDS``.
        parameters: Options of the CLI's own, listed after the shared ones and handed over as ``extra``.
        examples: Example lines of the CLI's own, listed after the shared ones.
    """
    def act(ctx: Any, values: Mapping[str, Any], extra: Mapping[str, object]) -> int:
        """Builds the request from the parsed values and hands it to the service."""
        return service.build(BuildRequest(
            build_type=values["build_type"].value,
            sanitizers=parse_sanitizers(values["sanitize"], sanitizers),
            defines=tuple(values["define"] or ()),
            jobs=values["jobs"],
            tests=not values["no_test"],
            report=values["report"],
            extra=extra,
            obj=ctx.obj,
        ))

    shared = (type_option(build_types), sanitize_option(sanitizers), define_option(), jobs_option(),
              no_test_option(), report_option())
    sanitized = (f"{program} build --sanitize {sanitizers[0]}  # A tree of its own",) if sanitizers else ()
    epilog = "\n".join((
        f"{program} build",
        f"{program} build --type {build_types.names[-1]}  # The tree of that type",
        *sanitized,
        f"{program} build -D VAR=VALUE  # Pass a CMake cache variable to configure",
        f"{program} build --jobs 4 --no-test  # Four compile jobs, no test programs",
        *examples,
    ))
    app.command(K_BUILD, rich_help_panel=panel, epilog=epilog)(
        command_function(shared, parameters, act, K_BUILD_SUMMARY))
