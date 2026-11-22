# options.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Declares the options of ``build``, ``run``, ``bench`` and ``check``, so every CLI spells them alike."""

from __future__ import annotations

from typing import Optional

from .build_types import BuildTypes
from .command_parameter import CommandParameter


def type_option(build_types: BuildTypes, subject: str = "Build type") -> CommandParameter:
    """Returns the ``--type``/``-t`` parameter, named ``build_type``, over *build_types*.

    Args:
        build_types: The types the option offers and the one it takes when absent.
        subject: What the type chooses, the start of the help line, such as ``Tree to run from``.
    """
    import typer

    choice = build_types.choice()
    return CommandParameter(
        name="build_type",
        annotation=choice,
        default=typer.Option(
            choice(build_types.default), "--type", "-t", case_sensitive=False,
            help=f"{subject}: {' | '.join(build_types.names)}. Each type has a tree of its own. "
                 f"Default: {build_types.default}."),
    )


def define_option() -> CommandParameter:
    """Returns the ``--define``/``-D`` parameter, named ``define``, a repeatable ``VAR=VALUE``."""
    import typer

    return CommandParameter(
        name="define",
        annotation=Optional[list[str]],
        default=typer.Option(
            None, "--define", "-D", metavar="VAR=VALUE",
            help="Pass a CMake cache variable to configure. Repeatable. The tree keeps it on a "
                 "later build without the flag; pass VAR= to clear one."),
    )


def jobs_option() -> CommandParameter:
    """Returns the ``--jobs``/``-j`` parameter of ``build``, named ``jobs``, the compile job count."""
    import typer

    return CommandParameter(
        name="jobs",
        annotation=Optional[int],
        default=typer.Option(
            None, "--jobs", "-j", min=1, metavar="N",
            help="Compile jobs run at once. Default: one per hardware thread, or "
                 "CMAKE_BUILD_PARALLEL_LEVEL when it is set."),
    )


def no_test_option() -> CommandParameter:
    """Returns the ``--no-test`` parameter, named ``no_test``."""
    import typer

    return CommandParameter(
        name="no_test",
        annotation=bool,
        default=typer.Option(False, "--no-test", help="Build no test programs. Tests build by default."),
    )


def target_argument() -> CommandParameter:
    """Returns the optional ``TARGET`` argument of ``run``, named ``target``."""
    import typer

    return CommandParameter(
        name="target",
        annotation=Optional[str],
        default=typer.Argument(
            None, help="Program to run: its exact name, else a part of its name."),
    )


def no_build_option() -> CommandParameter:
    """Returns the ``--no-build`` parameter of ``run``, named ``no_build``."""
    import typer

    return CommandParameter(
        name="no_build",
        annotation=bool,
        default=typer.Option(
            False, "--no-build", help="Run what is already built, without building first."),
    )


def report_option() -> CommandParameter:
    """Returns the ``--report``/``-r`` parameter of ``check``, named ``report``."""
    import typer

    return CommandParameter(
        name="report",
        annotation=bool,
        default=typer.Option(
            False, "--report", "-r", help="Print the finding count of each rule without failing."),
    )


def rule_option() -> CommandParameter:
    """Returns the ``--rule`` parameter of ``check``, named ``rule``."""
    import typer

    return CommandParameter(
        name="rule",
        annotation=Optional[str],
        default=typer.Option(None, "--rule", metavar="NAME", help="Run only this rule."),
    )
