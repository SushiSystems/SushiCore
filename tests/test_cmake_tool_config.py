# test_cmake_tool_config.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests that the cmake driver reads only the tool paths and the expansion a config offers."""

from __future__ import annotations

import pytest

from sushicore.cmake_driver import CMakeDriver
from sushicore.console_memory import RecordingConsole
from sushicore.proc_memory import RecordingRunner


class _ToolPaths:
    """A config holding the three tool paths and the expansion, and nothing else."""

    def __init__(self, cmake_exe: str = "", ctest_exe: str = "", doxygen_exe: str = "") -> None:
        """Hold the three tool paths."""
        self.cmake_exe = cmake_exe
        self.ctest_exe = ctest_exe
        self.doxygen_exe = doxygen_exe

    def expand(self, value: str) -> str:
        """Expand a leading tilde to a fixed home."""
        return value.replace("~", "/home/me", 1)


def _driver() -> CMakeDriver:
    """Return a driver over a console and a runner that start nothing."""
    console = RecordingConsole()
    return CMakeDriver(console, RecordingRunner(console))


@pytest.mark.small
@pytest.mark.parametrize(("configured", "expected"), [("~/bin/cmake", "/home/me/bin/cmake"), ("", "cmake")],
                         ids=["a configured path is expanded", "none falls back to the name"])
def test_cmake_is_the_expanded_configured_path_or_its_name(configured, expected):
    """Check that the cmake executable comes from the config's field and its expansion."""
    assert _driver().cmake(_ToolPaths(cmake_exe=configured)) == expected


@pytest.mark.small
def test_ctest_is_the_expanded_configured_path():
    """Check that the ctest executable comes from the config's field and its expansion."""
    assert _driver().ctest(_ToolPaths(ctest_exe="~/bin/ctest")) == "/home/me/bin/ctest"
