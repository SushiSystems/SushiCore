# command_function.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Builds the Typer function of a canonical command from its parameters and the call it makes."""

from __future__ import annotations

import inspect
from typing import Any, Callable, Mapping, Sequence

from .command_parameter import CommandParameter
from .errors import ParameterNameError

K_CONTEXT_NAME = "ctx"

#: What a command does with the Typer context, the shared values and the CLI's own, each by name.
CommandAction = Callable[[Any, Mapping[str, object], Mapping[str, object]], int]


def command_function(
    shared: Sequence[CommandParameter], own: Sequence[CommandParameter], action: CommandAction,
    summary: str,
) -> Callable[..., None]:
    """Returns a function Typer registers as a command with *shared* and *own*, which exits with *action*'s code.

    Typer reads the signature, so the function takes the context and then each parameter by name.

    Args:
        shared: The parameters the canonical command declares, listed first on the help page.
        own: The parameters the CLI adds; *action* gets their values apart from the shared ones.
        action: Called with the context, the shared values and the CLI's own; returns the exit code.
        summary: The command's help text.

    Raises:
        ParameterNameError: Two parameters share a name, or one is named ``ctx``.
    """
    import typer

    parameters = [*shared, *own]
    names = [parameter.name for parameter in parameters]
    taken = sorted({name for name in names if names.count(name) > 1 or name == K_CONTEXT_NAME})
    if taken:
        raise ParameterNameError(f"the command declares {', '.join(taken)} more than once.")
    own_names = frozenset(parameter.name for parameter in own)

    def command(ctx: typer.Context, **values: object) -> None:
        """Runs the action with the shared values apart from the CLI's own, and exits with its code."""
        raise typer.Exit(action(
            ctx,
            {name: value for name, value in values.items() if name not in own_names},
            {name: value for name, value in values.items() if name in own_names},
        ))

    context = inspect.Parameter(
        K_CONTEXT_NAME, inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=typer.Context)
    declared = [
        inspect.Parameter(parameter.name, inspect.Parameter.KEYWORD_ONLY,
                          default=parameter.default, annotation=parameter.annotation)
        for parameter in parameters
    ]
    command.__signature__ = inspect.Signature([context, *declared], return_annotation=None)
    command.__annotations__ = {
        K_CONTEXT_NAME: typer.Context,
        **{parameter.name: parameter.annotation for parameter in parameters},
        "return": None,
    }
    command.__doc__ = summary
    return command
