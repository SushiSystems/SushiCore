# test_docker_console.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests that the docker commands run against a console holding only the four calls they declare."""

from pathlib import Path

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.docker import DockerEnvironment, DockerImage
from sushicore.proc_memory import RecordingRunner

pytestmark = pytest.mark.small


class _FourCalls:
    """A console holding header, info, success and error, and nothing else."""

    def __init__(self) -> None:
        """Start with no message."""
        self.messages: list[tuple[str, str]] = []

    def header(self, title: str, /) -> None:
        """Record a section title."""
        self.messages.append(("header", title))

    def info(self, msg: str, /) -> None:
        """Record an informational message."""
        self.messages.append(("info", msg))

    def success(self, msg: str, /) -> None:
        """Record a success message."""
        self.messages.append(("success", msg))

    def error(self, msg: str, /) -> None:
        """Record an error."""
        self.messages.append(("error", msg))


def test_build_and_run_print_through_a_console_with_only_the_declared_calls():
    console = _FourCalls()
    environment = DockerEnvironment(DockerImage("sushitrack", "/workspace/sushitrack"), Path("root"),
                                    console, RecordingRunner(RecordingConsole()))
    environment.build(no_cache=True)
    environment.run(gpus=False)
    assert [kind for kind, _ in console.messages] == ["header", "info", "success", "header", "info"]
