# test_run_program.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Running one built program: the target, the pick and the default."""

import os
import stat
from pathlib import Path

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.discovery import ExecutableIndex
from sushicore.proc_memory import RecordingRunner
from sushicore.run_program import run_program


pytestmark = pytest.mark.medium

K_EXIT = 7


def _exe(directory: Path, name: str) -> Path:
    """Create a file that the executable walk recognizes, regardless of platform."""
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{name}.exe"
    path.write_text("")
    if os.name != "nt":
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return path


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """A checkout that registers one example and builds it beside a test program."""
    examples = tmp_path / "applications" / "examples"
    examples.mkdir(parents=True)
    (examples / "CMakeLists.txt").write_text("add_executable(demo demo.cpp)\n", encoding="utf-8")
    tree = tmp_path / "build" / "default-debug"
    _exe(tree, "alpha_tests")
    _exe(tree, "demo")
    return tmp_path


def _run(project: Path, answer: str | None = None, **options):
    """Runs through recorders and returns the exit code, the runner and the console."""
    console = RecordingConsole(answer=answer)
    runner = RecordingRunner(console)
    runner.script(K_EXIT)
    code = run_program(
        ExecutableIndex(), console, runner, build_dir=project / "build" / "default-debug",
        project_root=project, env={"K": "v"}, **options)
    return code, runner, console


def test_a_target_runs_with_the_arguments_the_environment_and_the_root(project):
    code, runner, _ = _run(project, target="alpha", app_args=["--flag"])

    command = runner.commands[0]
    assert code == K_EXIT
    assert (Path(command.argv[0]).stem, command.argv[1:]) == ("alpha_tests", ("--flag",))
    assert (command.cwd, command.env) == (project, {"K": "v"})


def test_a_pick_lists_the_example_and_runs_it(project):
    code, runner, console = _run(project, answer="1", pick=True)

    assert code == K_EXIT
    assert Path(runner.commands[0].argv[0]).stem == "demo"
    assert console.texts("info") == ["Executing: demo.exe"]


def test_a_pick_with_list_all_reaches_a_program_that_is_not_an_example(project):
    _, runner, _ = _run(project, answer="1", pick=True, list_all=True)

    assert Path(runner.commands[0].argv[0]).stem == "alpha_tests"


def test_the_default_runs_when_no_target_is_given(project):
    _, runner, _ = _run(project, default="demo")

    assert Path(runner.commands[0].argv[0]).stem == "demo"


def test_a_target_that_matches_nothing_returns_one_and_starts_nothing(project):
    code, runner, console = _run(project, target="gadget")

    assert (code, runner.commands) == (1, [])
    assert console.texts("error") == ["Executable matching 'gadget' not found."]
