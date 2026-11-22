# test_check_command.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests that the shared check command asks the CLI's service for every rule or one."""

import pytest
import typer
from typer.testing import CliRunner

from sushicore.command_surface import CheckRequest, register_check_command

pytestmark = pytest.mark.small


class _RecordingCheck:
    """Records each request and answers the exit code it was given."""

    def __init__(self, code: int = 0) -> None:
        self.requests: list[CheckRequest] = []
        self._code = code

    def check(self, request: CheckRequest) -> int:
        self.requests.append(request)
        return self._code


def _app(service: _RecordingCheck) -> typer.Typer:
    app = typer.Typer()

    @app.callback()
    def root() -> None:
        """Root."""

    register_check_command(app, service, program="sx")
    return app


def test_check_without_flags_asks_for_every_rule_and_a_verdict():
    service = _RecordingCheck()
    CliRunner().invoke(_app(service), ["check"])
    assert service.requests == [CheckRequest()]


def test_check_hands_the_report_flag_and_the_one_rule_to_the_service():
    service = _RecordingCheck()
    CliRunner().invoke(_app(service), ["check", "-r", "--rule", "rule_console_output"])
    assert service.requests == [CheckRequest(report=True, rule="rule_console_output")]


def test_check_exits_with_the_code_the_service_returns():
    assert CliRunner().invoke(_app(_RecordingCheck(code=1)), ["check"]).exit_code == 1


def test_check_is_listed_under_the_build_panel():
    command = typer.main.get_command(_app(_RecordingCheck())).commands["check"]
    assert command.rich_help_panel == "Build"
