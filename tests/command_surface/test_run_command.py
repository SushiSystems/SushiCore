# test_run_command.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests that the shared run command turns its flags and forwarded arguments into one request."""

import io

import pytest
import typer
from typer.testing import CliRunner

from sushicore.aliases import Alias, AliasTable
from sushicore.command_surface import BuildTypes, CommandParameter, RunRequest, register_run_command

pytestmark = pytest.mark.small


class _RecordingRun:
    """Records each request and answers exit code 0."""

    def __init__(self) -> None:
        self.requests: list[RunRequest] = []

    def run(self, request: RunRequest) -> int:
        self.requests.append(request)
        return 0


def _app(service: _RecordingRun, **keywords) -> typer.Typer:
    app = typer.Typer()

    @app.callback()
    def root() -> None:
        """Root."""

    register_run_command(app, service, program="sx",
                         build_types=BuildTypes(("debug", "release"), "debug"), **keywords)
    return app


def test_run_without_flags_asks_for_no_program_and_a_build_first():
    service = _RecordingRun()
    CliRunner().invoke(_app(service), ["run"])
    assert service.requests == [RunRequest(build_type="debug")]


def test_run_hands_the_target_the_flags_and_the_arguments_after_the_separator():
    service = _RecordingRun()
    CliRunner().invoke(_app(service), ["run", "demo", "--no-build", "--", "--gtest_filter=A.*", "-v"])
    assert service.requests == [RunRequest(
        build_type="debug", target="demo", build=False, arguments=("--gtest_filter=A.*", "-v"))]


def test_run_hands_the_pick_over_every_program():
    service = _RecordingRun()
    CliRunner().invoke(_app(service), ["run", "--pick", "--all"])
    assert service.requests == [RunRequest(build_type="debug", pick=True, list_all=True)]


def test_run_takes_the_old_spelling_of_pick_from_the_alias_table():
    service = _RecordingRun()
    table = AliasTable("sx", (Alias("sx run --select", "sx run --pick", None),), stream=io.StringIO(),
                       environ={})
    CliRunner().invoke(_app(service, aliases=table, old_pick=("--select", "-s")), ["run", "-s"])
    assert service.requests[0].pick is True


def test_run_declares_no_old_spelling_without_an_alias_table():
    command = typer.main.get_command(_app(_RecordingRun())).commands["run"]
    assert "--sort" not in {name for parameter in command.params for name in parameter.opts}


def test_run_hands_a_clis_own_option_over_as_extra():
    service = _RecordingRun()
    role = CommandParameter("role", str, typer.Option("master", "--role"))
    CliRunner().invoke(_app(service, parameters=[role]), ["run", "--role", "worker"])
    assert service.requests[0].extra == {"role": "worker"}


def test_run_hands_the_type_over():
    service = _RecordingRun()
    CliRunner().invoke(_app(service), ["run", "-t", "release"])
    assert service.requests == [RunRequest(build_type="release")]


def test_run_refuses_a_type_outside_its_build_types_before_the_service_runs():
    service = _RecordingRun()
    result = CliRunner().invoke(_app(service), ["run", "--type", "minsizerel"])
    assert (result.exit_code, service.requests) == (2, [])
