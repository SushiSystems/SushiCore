# test_command_function.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests that a declared command parses its parameters and hands the CLI's own values apart."""

import pytest
import typer
from typer.testing import CliRunner

from sushicore.command_surface import CommandParameter, ParameterNameError
from sushicore.command_surface.command_function import command_function

pytestmark = pytest.mark.small


def _flag(name: str) -> CommandParameter:
    return CommandParameter(name, bool, typer.Option(False, "--" + name.replace("_", "-")))


def _invoke(arguments: list, calls: list) -> int:
    def act(ctx, shared, own):
        calls.append((dict(shared), dict(own)))
        return 7

    app = typer.Typer()

    @app.callback()
    def root() -> None:
        """Root."""

    app.command("go")(command_function([_flag("fast")], [_flag("loud")], act, "Go."))
    return CliRunner().invoke(app, ["go", *arguments]).exit_code


def test_command_function_hands_the_shared_values_apart_from_the_clis_own():
    calls = []
    _invoke(["--loud"], calls)
    assert calls == [({"fast": False}, {"loud": True})]


def test_command_function_exits_with_the_code_the_action_returns():
    assert _invoke([], []) == 7


@pytest.mark.parametrize("names", [("fast", "fast"), ("ctx",)])
def test_command_function_refuses_a_name_taken_twice(names):
    with pytest.raises(ParameterNameError):
        command_function([_flag(name) for name in names], [], lambda ctx, shared, own: 0, "Go.")


def test_command_function_refuses_a_clis_parameter_that_repeats_a_shared_name():
    with pytest.raises(ParameterNameError, match="fast"):
        command_function([_flag("fast")], [_flag("fast")], lambda ctx, shared, own: 0, "Go.")
