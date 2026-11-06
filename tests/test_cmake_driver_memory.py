# test_cmake_driver_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What the in-memory CMake driver adds to the port's contract: configured trees, scripts, records."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from sushicore.cmake_driver_memory import MemoryCMakeDriver
from sushicore.console_memory import RecordingConsole

pytestmark = pytest.mark.small

K_BUILD = Path("build")
K_CFG = SimpleNamespace(cmake_exe="", ctest_exe="", doxygen_exe="", expand=lambda text: text)


def test_a_configure_leaves_the_tree_its_argv_names():
    driver = MemoryCMakeDriver(RecordingConsole())
    driver.configure(["cmake", "-S", ".", "-B", "build", "-G", "Ninja",
                      "-DCMAKE_BUILD_TYPE:STRING=Debug"], Path("."))
    assert driver.cached_value(K_BUILD, "CMAKE_BUILD_TYPE") == "Debug"
    assert not driver.needs_configure(K_BUILD, "Ninja")


def test_a_command_returns_the_scripted_code_then_zero():
    driver = MemoryCMakeDriver(RecordingConsole()).script(2)
    assert driver.compile(K_CFG, K_BUILD, Path("."), None) == 2
    assert driver.compile(K_CFG, K_BUILD, Path("."), None) == 0


def test_a_build_with_no_configuration_records_the_tree_s_own():
    driver = MemoryCMakeDriver(RecordingConsole()).add_tree(K_BUILD, cache={"CMAKE_BUILD_TYPE": "Debug"})
    driver.compile(K_CFG, K_BUILD, Path("."), None, targets=["app"])
    assert [(call.method, call.arguments["config"], call.arguments["targets"])
            for call in driver.calls] == [("compile", "Debug", ("app",))]


def test_a_known_doxyfile_runs():
    driver = MemoryCMakeDriver(RecordingConsole(), doxyfiles=[Path("Doxyfile")])
    assert driver.doxygen(K_CFG, Path("Doxyfile"), Path("."), None) == 0
    assert [call.method for call in driver.calls] == ["doxygen"]
