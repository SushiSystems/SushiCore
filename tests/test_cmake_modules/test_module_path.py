# test_module_path.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Where a configure finds SushiCore's CMake modules, and that the entry module reaches each of them."""

import re
from pathlib import Path

import pytest

from sushicore.cmake_modules import K_CMAKE_MODULES, with_cmake_modules

K_FOLDER = Path("/opt/sushicore/cmake")

#: The script the test-size step runs with ``cmake -P``; it is never included.
K_SCRIPT = "SushiCheckTestSizes.cmake"


@pytest.mark.small
def test_with_cmake_modules_appends_the_definition_to_an_argv_without_one():
    assert with_cmake_modules(["cmake", "-B", "tree"], K_FOLDER) == [
        "cmake", "-B", "tree", "-DCMAKE_MODULE_PATH=/opt/sushicore/cmake"]


@pytest.mark.small
@pytest.mark.parametrize("given, merged", [
    ("-DCMAKE_MODULE_PATH=/repo/cmake", "-DCMAKE_MODULE_PATH=/repo/cmake;/opt/sushicore/cmake"),
    ("-DCMAKE_MODULE_PATH:PATH=/repo/cmake", "-DCMAKE_MODULE_PATH:PATH=/repo/cmake;/opt/sushicore/cmake"),
    ("-DCMAKE_MODULE_PATH=/opt/sushicore/cmake", "-DCMAKE_MODULE_PATH=/opt/sushicore/cmake"),
])
def test_with_cmake_modules_keeps_the_callers_folders_first_and_adds_the_folder_once(given, merged):
    assert with_cmake_modules(["cmake", given, "-B", "tree"], K_FOLDER) == ["cmake", merged, "-B", "tree"]


@pytest.mark.small
def test_with_cmake_modules_leaves_an_entry_that_only_starts_with_the_name():
    argv = ["cmake", "-DCMAKE_MODULE_PATH_EXTRA=x"]
    assert with_cmake_modules(argv, K_FOLDER) == [*argv, "-DCMAKE_MODULE_PATH=/opt/sushicore/cmake"]


@pytest.mark.medium
def test_the_entry_module_includes_every_module_of_the_folder():
    entry = (K_CMAKE_MODULES / "SushiBuild.cmake").read_text(encoding="utf-8")
    included = set(re.findall(r'include\("\$\{CMAKE_CURRENT_LIST_DIR\}/(\w+\.cmake)"\)', entry))
    modules = {path.name for path in K_CMAKE_MODULES.glob("*.cmake")} - {"SushiBuild.cmake", K_SCRIPT}
    assert included == modules
