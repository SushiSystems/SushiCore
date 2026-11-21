# test_clean_command.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The shared `clean` command: which trees a filter selects, and that only --sure removes them."""

from dataclasses import dataclass, field
from pathlib import Path

import pytest
import typer
from typer.testing import CliRunner

from sushicore.build_tree import tree_dir
from sushicore.clean_command import clean_trees, register_clean_command, select_trees
from sushicore.console_memory import RecordingConsole


pytestmark = pytest.mark.medium

K_NAMES = {None: "default", "address": "asan", "thread": "tsan"}
K_TYPES = ("debug", "release")


class _Driver:
    """Records the trees it was asked to remove, and removes nothing."""

    def __init__(self) -> None:
        self.removed: list[Path] = []

    def clean_tree(self, build_dir: Path) -> None:
        self.removed.append(build_dir)


@dataclass
class _Target:
    """A checkout whose console and driver record."""

    root: Path
    console: RecordingConsole = field(default_factory=RecordingConsole)
    driver: _Driver = field(default_factory=_Driver)


@pytest.fixture
def target(tmp_path: Path) -> _Target:
    """A checkout holding four trees: default-debug, default-release, asan-release, tsan-debug."""
    for name, build_type in (("default", "debug"), ("default", "release"),
                             ("asan", "release"), ("tsan", "debug")):
        tree_dir(tmp_path, name, build_type).mkdir(parents=True)
    return _Target(tmp_path)


def _names(root: Path, trees: list[Path]) -> list[str]:
    """Returns the tree folder names, relative to the build folder."""
    return sorted(tree.relative_to(root / "build").as_posix() for tree in trees)


def test_no_filter_selects_every_tree(target):
    trees = select_trees(target.root, K_NAMES, K_TYPES)

    assert _names(target.root, trees) == [
        "asan-release", "default-debug", "default-release", "tsan-debug"]


def test_a_type_selects_the_plain_tree_of_that_type_only(target):
    trees = select_trees(target.root, K_NAMES, K_TYPES, types=("debug",))

    assert _names(target.root, trees) == ["default-debug"]


def test_a_sanitizer_selects_its_trees_in_every_type(target):
    trees = select_trees(target.root, K_NAMES, K_TYPES, sanitizers=("address",))

    assert _names(target.root, trees) == ["asan-release"]


def test_a_type_and_a_sanitizer_select_the_tree_of_both(target):
    trees = select_trees(target.root, K_NAMES, K_TYPES, types=("debug",), sanitizers=("thread",))

    assert _names(target.root, trees) == ["tsan-debug"]


def test_a_tree_that_does_not_exist_is_not_selected(target):
    trees = select_trees(target.root, K_NAMES, K_TYPES, types=("release",), sanitizers=("thread",))

    assert trees == []


def test_without_sure_nothing_is_removed_and_the_code_says_so(target):
    trees = select_trees(target.root, K_NAMES, K_TYPES)

    code = clean_trees(target, trees, sure=False)

    assert (code, target.driver.removed) == (2, [])
    assert target.console.texts("error") == ["Nothing was removed. Add --sure to remove the trees above."]


def test_with_sure_every_listed_tree_is_removed(target):
    trees = select_trees(target.root, K_NAMES, K_TYPES, types=("debug",))

    code = clean_trees(target, trees, sure=True)

    assert (code, target.driver.removed) == (0, trees)


def test_no_tree_is_a_success_that_removes_nothing(tmp_path):
    empty = _Target(tmp_path)

    assert clean_trees(empty, [], sure=False) == 0
    assert empty.console.texts("info") == ["No build tree to remove."]


def _app(target: _Target, names=K_NAMES) -> typer.Typer:
    """An application with the shared clean command over *target*."""
    app = typer.Typer(name="sx", add_completion=False)

    @app.command("other")
    def other() -> None:
        """Another command, so `clean` is a command and not the whole application."""

    register_clean_command(
        app, lambda ctx: target, program="sx", panel="Project", names=names, build_types=K_TYPES)
    return app


def test_the_command_removes_the_selected_tree_with_sure(target):
    result = CliRunner().invoke(_app(target), ["clean", "--type", "debug", "--sure"])

    assert result.exit_code == 0
    assert target.driver.removed == [tree_dir(target.root, "default", "debug")]


def test_the_command_without_sure_exits_two_and_removes_nothing(target):
    result = CliRunner().invoke(_app(target), ["clean"])

    assert result.exit_code == 2
    assert target.driver.removed == []


def test_the_command_refuses_a_build_type_the_cli_does_not_build(target):
    result = CliRunner().invoke(_app(target), ["clean", "--type", "profile", "--sure"])

    assert result.exit_code == 2
    assert target.driver.removed == []


def test_the_command_takes_the_short_type_flag_and_a_sanitizer(target):
    result = CliRunner().invoke(_app(target), ["clean", "-t", "release", "--sanitize", "address", "--sure"])

    assert result.exit_code == 0
    assert target.driver.removed == [tree_dir(target.root, "asan", "release")]
