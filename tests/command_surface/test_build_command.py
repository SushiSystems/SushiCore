# test_build_command.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests that the shared build command turns its flags into one request for the CLI's service."""

import pytest
import typer
from typer.testing import CliRunner

from sushicore.command_surface import BuildRequest, BuildTypes, CommandParameter, register_build_command

pytestmark = pytest.mark.small


class _RecordingBuild:
    """Records each request and answers the exit code it was given."""

    def __init__(self, code: int = 0) -> None:
        self.requests: list[BuildRequest] = []
        self._code = code

    def build(self, request: BuildRequest) -> int:
        self.requests.append(request)
        return self._code


def _app(service: _RecordingBuild, **keywords) -> typer.Typer:
    app = typer.Typer()

    @app.callback()
    def root(ctx: typer.Context) -> None:
        """Root."""
        ctx.obj = "workspace"

    register_build_command(app, service, program="sx",
                           build_types=BuildTypes(("debug", "release"), "debug"), **keywords)
    return app


def test_build_without_flags_asks_for_the_default_type_with_tests():
    service = _RecordingBuild()
    CliRunner().invoke(_app(service), ["build"])
    assert service.requests == [BuildRequest(build_type="debug", obj="workspace")]


def test_build_hands_every_shared_flag_to_the_service():
    service = _RecordingBuild()
    CliRunner().invoke(_app(service), [
        "build", "-t", "release", "--sanitize", "undefined,address", "-D", "A=1", "--define", "B=",
        "-j", "4", "--no-test", "-r"])
    assert service.requests == [BuildRequest(
        build_type="release", sanitizers=("address", "undefined"), defines=("A=1", "B="), jobs=4,
        tests=False, report=True, obj="workspace")]


def test_build_exits_with_the_code_the_service_returns():
    assert CliRunner().invoke(_app(_RecordingBuild(code=5)), ["build"]).exit_code == 5


@pytest.mark.parametrize("arguments", [
    ["--type", "minsizerel"], ["--sanitize", "memory"], ["--sanitize", "address,thread"], ["-j", "0"],
])
def test_build_refuses_a_value_outside_the_shared_surface_before_the_service_runs(arguments):
    service = _RecordingBuild()
    result = CliRunner().invoke(_app(service), ["build", *arguments])
    assert (result.exit_code, service.requests) == (2, [])


def test_build_refuses_a_sanitizer_the_cli_does_not_build():
    service = _RecordingBuild()
    result = CliRunner().invoke(_app(service, sanitizers=("thread",)), ["build", "--sanitize", "address"])
    assert (result.exit_code, service.requests) == (2, [])


def test_build_hands_a_clis_own_option_over_as_extra():
    service = _RecordingBuild()
    role = CommandParameter("role", str, typer.Option("master", "--role"))
    CliRunner().invoke(_app(service, parameters=[role]), ["build", "--role", "worker"])
    assert service.requests[0].extra == {"role": "worker"}


def test_build_is_listed_under_the_panel_it_is_given():
    command = typer.main.get_command(_app(_RecordingBuild(), panel="Project")).commands["build"]
    assert command.rich_help_panel == "Project"


def test_build_declares_the_canonical_flags():
    command = typer.main.get_command(_app(_RecordingBuild())).commands["build"]
    names = {name for parameter in command.params for name in parameter.opts}
    assert names == {"--type", "-t", "--sanitize", "--define", "-D", "--jobs", "-j", "--no-test",
                     "--report", "-r"}
