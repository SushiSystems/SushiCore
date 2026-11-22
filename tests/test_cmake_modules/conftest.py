# conftest.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Fixtures that run CMake on the fixture projects beside this file, with the modules on its path.

A test that needs CMake 3.29, Ninja or a C++ compiler the machine lacks is skipped with the reason.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pytest

from sushicore.cmake_modules import K_CMAKE_MODULES, with_cmake_modules

#: The folder of the fixture projects.
K_FIXTURES = Path(__file__).resolve().parent / "fixtures"

#: The oldest CMake the modules accept.
K_CMAKE_FLOOR = (3, 29)

#: The compilers a configure takes, the first found on the search path first.
K_COMPILERS = ("clang++", "g++")


@dataclass(frozen=True, slots=True)
class CMakeRun:
    """Holds what one cmake call printed and the tree it wrote."""

    code: int
    output: str
    tree: Path

    def says(self, text: str) -> bool:
        """Return whether the output holds *text*, with CMake's line wrapping read as one space."""
        return " ".join(text.split()) in " ".join(self.output.split())

    def link_block(self, stem: str) -> str:
        """Return the build.ninja statement that links the output named *stem*, with its variables.

        The output may carry a platform prefix and suffix: ``libdemo_high.so``, ``demo_high.dll``,
        ``marked.exe``.
        """
        text = (self.tree / "build.ninja").read_text(encoding="utf-8")
        pattern = rf"^build (?:lib)?{re.escape(stem)}(?:\.exe|\.dll|\.so)?[ :].*?(?=^\S|\Z)"
        match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
        assert match is not None, f"build.ninja links no output named {stem}"
        return match.group(0)

    def compile_command(self, source: str) -> str:
        """Return the compile command compile_commands.json records for the source *source*."""
        entries = json.loads((self.tree / "compile_commands.json").read_text(encoding="utf-8"))
        commands = [entry["command"] for entry in entries if Path(entry["file"]).name == source]
        assert len(commands) == 1, f"compile_commands.json holds {len(commands)} for {source}"
        return commands[0]


@pytest.fixture(scope="session")
def cmake_program() -> str:
    """Return the cmake on the search path, or skip when there is none or it is older than 3.29."""
    program = shutil.which("cmake")
    if program is None:
        pytest.skip("no cmake on the search path")
    printed = subprocess.run(
        [program, "--version"], capture_output=True, text=True, check=True).stdout
    found = re.search(r"(\d+)\.(\d+)", printed)
    if found is None or (int(found.group(1)), int(found.group(2))) < K_CMAKE_FLOOR:
        pytest.skip(
            f"the CMake modules need CMake 3.29 or later; the path has {printed.splitlines()[0]}")
    return program


@pytest.fixture(scope="session")
def configure_args(cmake_program) -> list[str]:
    """Return the arguments of a Ninja Debug configure, or skip without Ninja or a C++ compiler."""
    ninja = shutil.which("ninja")
    if ninja is None:
        pytest.skip("no ninja on the search path")
    compilers = [path for path in map(shutil.which, K_COMPILERS) if path is not None]
    if not compilers:
        pytest.skip(f"no C++ compiler on the search path; looked for {', '.join(K_COMPILERS)}")
    if sys.platform == "win32" and "LIB" not in os.environ:
        pytest.skip("a Windows configure links through the Windows SDK, and no developer "
                    "environment (vcvars) set LIB")
    return [cmake_program, "-G", "Ninja", f"-DCMAKE_MAKE_PROGRAM={ninja}",
            f"-DCMAKE_CXX_COMPILER={compilers[0]}", "-DCMAKE_BUILD_TYPE=Debug"]


@pytest.fixture(scope="session")
def configure(configure_args, tmp_path_factory) -> Callable[..., CMakeRun]:
    """Return a function that configures one fixture project in a fresh tree with *definitions*."""

    def run(project: str, *definitions: str) -> CMakeRun:
        tree = tmp_path_factory.mktemp(project)
        argv = with_cmake_modules(
            [*configure_args, *definitions, "-S", str(K_FIXTURES / project), "-B", str(tree)])
        done = subprocess.run(argv, capture_output=True, text=True)
        return CMakeRun(done.returncode, done.stdout + done.stderr, tree)

    return run


@pytest.fixture(scope="session")
def build_target(cmake_program) -> Callable[[CMakeRun, str], CMakeRun]:
    """Return a function that builds one target of a configured tree."""

    def run(configured: CMakeRun, target: str) -> CMakeRun:
        argv = [cmake_program, "--build", str(configured.tree), "--target", target]
        done = subprocess.run(argv, capture_output=True, text=True)
        return CMakeRun(done.returncode, done.stdout + done.stderr, configured.tree)

    return run


@pytest.fixture(scope="session")
def run_script(cmake_program, tmp_path_factory) -> Callable[[str], CMakeRun]:
    """Return a function that runs CMake script text with ``cmake -P``, the modules' folder at hand.

    The text reads the folder as ``SUSHI_MODULES``; script mode needs no compiler.
    """

    def run(text: str) -> CMakeRun:
        folder = tmp_path_factory.mktemp("script")
        script = folder / "script.cmake"
        script.write_text(text, encoding="utf-8")
        argv = [cmake_program, f"-DSUSHI_MODULES={K_CMAKE_MODULES.as_posix()}", "-P", str(script)]
        done = subprocess.run(argv, capture_output=True, text=True)
        return CMakeRun(done.returncode, done.stdout + done.stderr, folder)

    return run


@pytest.fixture(scope="session")
def basic_tree(configure) -> CMakeRun:
    """Return the basic fixture configured once with every module's defaults."""
    return configure("basic")


@pytest.fixture(scope="session")
def tiers_tree(configure) -> CMakeRun:
    """Return the tier fixture configured once, with no refused call turned on."""
    return configure("tiers")
