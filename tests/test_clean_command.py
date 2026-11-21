# test_clean_command.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The shared `clean` command: which trees a filter selects, and that only --yes removes them."""

from dataclasses import dataclass, field
from pathlib import Path

import pytest
import typer
from typer.testing import CliRunner

from sushicore.build_tree import tree_dir
from sushicore.clean_command import (
    CleanExtra, clean_trees, register_clean_command, select_trees, tree_size)
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


def test_without_yes_nothing_is_removed_and_the_code_says_so(target):
    trees = select_trees(target.root, K_NAMES, K_TYPES)

    code = clean_trees(target, trees, yes=False)

    assert (code, target.driver.removed) == (2, [])
    assert target.console.texts("error") == ["Nothing was removed. Add --yes to remove them."]


def test_with_yes_every_listed_tree_is_removed(target):
    trees = select_trees(target.root, K_NAMES, K_TYPES, types=("debug",))

    code = clean_trees(target, trees, yes=True)

    assert (code, target.driver.removed) == (0, trees)


def test_no_tree_is_a_success_that_removes_nothing(tmp_path):
    empty = _Target(tmp_path)

    assert clean_trees(empty, [], yes=False) == 0
    assert empty.console.texts("info") == ["No build tree to remove."]


def _app(target: _Target, names=K_NAMES, type_trees=None, whole_build=False) -> typer.Typer:
    """An application with the shared clean command over *target*."""
    app = typer.Typer(name="sx", add_completion=False)

    @app.command("other")
    def other() -> None:
        """Another command, so `clean` is a command and not the whole application."""

    register_clean_command(
        app, lambda ctx: target, program="sx", panel="Project", names=names, build_types=K_TYPES,
        type_trees=type_trees, whole_build=whole_build)
    return app


def test_the_command_removes_the_selected_tree_with_yes(target):
    result = CliRunner().invoke(_app(target), ["clean", "--type", "debug", "--yes"])

    assert result.exit_code == 0
    assert target.driver.removed == [tree_dir(target.root, "default", "debug")]


def test_the_command_without_yes_exits_two_and_removes_nothing(target):
    result = CliRunner().invoke(_app(target), ["clean"])

    assert result.exit_code == 2
    assert target.driver.removed == []


def test_the_command_refuses_a_build_type_the_cli_does_not_build(target):
    result = CliRunner().invoke(_app(target), ["clean", "--type", "profile", "--yes"])

    assert result.exit_code == 2
    assert target.driver.removed == []


def test_the_command_takes_the_short_type_flag_and_a_sanitizer(target):
    result = CliRunner().invoke(_app(target), ["clean", "-t", "release", "--sanitize", "address", "--yes"])

    assert result.exit_code == 0
    assert target.driver.removed == [tree_dir(target.root, "asan", "release")]


K_ASAN_AS_TYPE = {"asan": "asan-release"}


def test_a_type_that_names_a_folder_selects_that_folder(target):
    trees = select_trees(target.root, {None: "default"}, K_TYPES, types=("asan",),
                         type_trees=K_ASAN_AS_TYPE)

    assert _names(target.root, trees) == ["asan-release"]


def test_no_filter_also_selects_the_folders_that_types_name(target):
    trees = select_trees(target.root, {None: "default"}, K_TYPES, type_trees=K_ASAN_AS_TYPE)

    assert _names(target.root, trees) == ["asan-release", "default-debug", "default-release"]


def test_the_command_removes_the_asan_tree_for_type_asan_and_no_other(target):
    app = _app(target, names={None: "default"}, type_trees=K_ASAN_AS_TYPE)

    result = CliRunner().invoke(app, ["clean", "--type", "asan", "--yes"])

    assert result.exit_code == 0
    assert target.driver.removed == [tree_dir(target.root, "asan", "release")]


def test_the_command_takes_the_short_yes_flag(target):
    result = CliRunner().invoke(_app(target), ["clean", "-t", "debug", "-y"])

    assert result.exit_code == 0
    assert target.driver.removed == [tree_dir(target.root, "default", "debug")]


def test_the_listing_says_what_would_be_removed_and_how_much_each_tree_holds(target):
    (tree_dir(target.root, "default", "debug") / "a.bin").write_bytes(b"x" * 2048)

    clean_trees(target, [tree_dir(target.root, "default", "debug")], yes=False)

    lines = target.console.texts("info")
    assert lines[0] == "These build trees would be removed:"
    assert lines[1].endswith("default-debug  (2.0 KiB)")


def test_the_listing_of_a_removal_says_so(target):
    clean_trees(target, [tree_dir(target.root, "default", "debug")], yes=True)

    assert target.console.texts("info")[0] == "Removing these build trees:"


def test_the_size_counts_the_files_of_every_folder_below_the_tree(tmp_path):
    (tmp_path / "x" / "y").mkdir(parents=True)
    (tmp_path / "x" / "y" / "a.bin").write_bytes(b"1" * 10)
    (tmp_path / "b.bin").write_bytes(b"2" * 5)

    assert tree_size(tmp_path) == 15


def test_all_selects_the_whole_build_folder_when_the_cli_offers_it(target):
    app = _app(target, whole_build=True)

    result = CliRunner().invoke(app, ["clean", "--all", "--yes"])

    assert result.exit_code == 0
    assert target.driver.removed == [target.root / "build"]


def test_all_takes_no_type(target):
    app = _app(target, whole_build=True)

    result = CliRunner().invoke(app, ["clean", "--all", "--type", "debug", "--yes"])

    assert result.exit_code == 2
    assert target.driver.removed == []


def test_all_is_refused_by_a_cli_that_does_not_offer_it(target):
    result = CliRunner().invoke(_app(target), ["clean", "--all", "--yes"])

    assert result.exit_code == 2
    assert target.driver.removed == []


def _app_with(target: _Target, **options) -> typer.Typer:
    """An application with the shared clean command and the given optional arguments."""
    app = typer.Typer(name="sx", add_completion=False)

    @app.command("other")
    def other() -> None:
        """Another command, so `clean` is a command and not the whole application."""

    register_clean_command(
        app, lambda ctx: target, program="sx", panel="Project", names=K_NAMES,
        build_types=K_TYPES, **options)
    return app


def test_a_full_clean_also_removes_the_folders_with_all_names(target):
    package = target.root / "package"
    package.mkdir()
    app = _app_with(target, with_all=lambda found: [found.root / "package"])

    result = CliRunner().invoke(app, ["clean", "--yes"])

    assert result.exit_code == 0
    assert package in target.driver.removed


def test_a_narrowed_clean_leaves_the_folders_with_all_names_alone(target):
    package = target.root / "package"
    package.mkdir()
    app = _app_with(target, with_all=lambda found: [found.root / "package"])

    CliRunner().invoke(app, ["clean", "--type", "debug", "--yes"])

    assert package not in target.driver.removed


def test_the_extra_flag_selects_its_own_folders_instead_of_the_trees(target):
    predictions = target.root / "pred"
    predictions.mkdir()
    extra = CleanExtra("--predictions", "Select the prediction folders.",
                       lambda found: [found.root / "pred"])
    app = _app_with(target, extra=extra)

    result = CliRunner().invoke(app, ["clean", "--predictions", "--yes"])

    assert result.exit_code == 0
    assert target.driver.removed == [predictions]


def test_the_extra_flag_takes_no_type(target):
    extra = CleanExtra("--predictions", "Select the prediction folders.", lambda found: [])
    app = _app_with(target, extra=extra)

    result = CliRunner().invoke(app, ["clean", "--predictions", "--type", "debug", "--yes"])

    assert result.exit_code == 2
    assert target.driver.removed == []
