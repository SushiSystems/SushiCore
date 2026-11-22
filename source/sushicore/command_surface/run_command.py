# run_command.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Registers the shared ``run`` command; the CLI hands it the service that starts a program."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Mapping, Optional, Sequence

from ..run_options import list_all_option, old_pick_option, pick_option
from .build_types import BuildTypes
from .command_function import command_function
from .command_parameter import CommandParameter
from .options import no_build_option, target_argument, type_option
from .panels import K_RUN_PANEL
from .run_service import RunRequest, RunService
from .verbs import K_RUN

if TYPE_CHECKING:
    import typer

    from ..aliases import AliasTable

K_RUN_SUMMARY = "Run a built program. Arguments after `--` go to it unchanged."
K_FORWARDING = {"allow_extra_args": True, "ignore_unknown_options": True}
K_OLD_PICK_FLAGS = ("--sort",)


def register_run_command(
    app: "typer.Typer", service: RunService, *, program: str, build_types: BuildTypes,
    panel: str = K_RUN_PANEL, aliases: Optional["AliasTable"] = None, old_pick: Sequence[str] = K_OLD_PICK_FLAGS,
    parameters: Sequence[CommandParameter] = (), examples: Sequence[str] = (),
) -> None:
    """Add ``run`` to *app*: ``TARGET``, ``--type``, ``--pick``, ``--all``, ``--no-build``, the arguments after ``--``.

    Args:
        app: The CLI's Typer application.
        service: Starts the program a request names.
        program: The CLI's command, such as ``sd``, which the examples are written with.
        build_types: The values of ``--type`` and its default.
        panel: The help panel the command is listed under.
        aliases: The CLI's alias table; with one, the hidden *old_pick* flags also mean ``--pick``,
            and the table must hold the row ``<program> run <first old flag>``.
        old_pick: The old flags of ``--pick``, declared only with *aliases*.
        parameters: Options of the CLI's own, listed after the shared ones and handed over as ``extra``.
        examples: Example lines of the CLI's own, listed after the shared ones.
    """
    def act(ctx: Any, values: Mapping[str, Any], extra: Mapping[str, object]) -> int:
        """Builds the request from the parsed values and hands it to the service."""
        return service.run(RunRequest(
            build_type=values["build_type"].value,
            target=values["target"],
            pick=bool(values["pick"] or values.get("old_pick")),
            list_all=values["list_all"],
            build=not values["no_build"],
            arguments=tuple(ctx.args),
            extra=extra,
            obj=ctx.obj,
        ))

    shared = [target_argument(), type_option(build_types, "Tree to run from"),
              CommandParameter("pick", bool, pick_option()),
              CommandParameter("list_all", bool, list_all_option()), no_build_option()]
    if aliases is not None:
        old = f"{program} {K_RUN} {old_pick[0]}"
        shared.append(CommandParameter("old_pick", bool, old_pick_option(aliases, old, *old_pick)))
    epilog = "\n".join((
        f"{program} run --pick  # Pick an example from a list",
        f"{program} run --pick --all  # Pick from every program, tests and benchmarks included",
        f"{program} run <program> --no-build  # Run what is built, building nothing",
        f"{program} run <program> -- --flag  # Arguments after -- go to the program",
        *examples,
    ))
    app.command(K_RUN, rich_help_panel=panel, epilog=epilog, context_settings=K_FORWARDING)(
        command_function(shared, parameters, act, K_RUN_SUMMARY))
