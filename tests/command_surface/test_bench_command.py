# test_bench_command.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests that the shared bench command asks the CLI's service for the benchmarks of one build type."""

import pytest
import typer
from typer.testing import CliRunner

from sushicore.command_surface import BenchRequest, BuildTypes, CommandParameter, register_bench_command

pytestmark = pytest.mark.small


class _RecordingBench:
    """Records each request and answers exit code 0."""

    def __init__(self) -> None:
        self.requests: list[BenchRequest] = []

    def bench(self, request: BenchRequest) -> int:
        self.requests.append(request)
        return 0


def _app(service: _RecordingBench, **keywords) -> typer.Typer:
    app = typer.Typer()

    @app.callback()
    def root() -> None:
        """Root."""

    register_bench_command(app, service, program="sx",
                           build_types=BuildTypes(("debug", "release"), "release"), **keywords)
    return app


def test_bench_without_flags_asks_for_the_default_type_of_the_benchmarks():
    service = _RecordingBench()
    CliRunner().invoke(_app(service), ["bench"])
    assert service.requests == [BenchRequest(build_type="release")]


def test_bench_hands_the_type_and_a_clis_own_option_to_the_service():
    service = _RecordingBench()
    filter = CommandParameter("filter", str, typer.Option("*", "--filter", "-f"))
    CliRunner().invoke(_app(service, parameters=[filter]), ["bench", "-t", "debug", "-f", "Gemm*"])
    assert service.requests == [BenchRequest(build_type="debug", extra={"filter": "Gemm*"})]


def test_bench_is_listed_under_the_run_panel():
    command = typer.main.get_command(_app(_RecordingBench())).commands["bench"]
    assert command.rich_help_panel == "Run"
