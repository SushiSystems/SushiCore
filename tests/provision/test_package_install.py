# test_package_install.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the install and archive step of the shared package command."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.provision.package_install import (K_STAGE_MARKER, CapturedRun,
                                                  PackageInstaller, install_summary)


def _lines(console, kind):
    """Return the text of every *kind* line the recording console took."""
    return [args[0] for name, args in console.calls if name == kind]


class _Runner:
    """Records commands and installs a file and a folder the way cmake --install would."""

    def __init__(self, install_code: int = 0) -> None:
        """Start with no calls; an install exits with *install_code*."""
        self.calls: list[list[str]] = []
        self.install_code = install_code

    def __call__(self, command, cwd, env=None) -> int:
        """Record *command*."""
        self.calls.append(command)
        return 0

    def capture(self, command, cwd, env=None) -> CapturedRun:
        """Record *command*; write a file and a folder into the prefix, as cmake prints them."""
        self.calls.append(command)
        if self.install_code != 0:
            return CapturedRun(self.install_code, "CMake Error: file cannot create directory")
        prefix = Path(command[command.index("--prefix") + 1])
        (prefix / "include").mkdir(parents=True, exist_ok=True)
        (prefix / "installed.txt").write_text("x")
        return CapturedRun(0, f"-- Installing: {prefix / 'include'}\n"
                              f"-- Installing: {prefix / 'installed.txt'}\n")


@pytest.fixture
def checkout(tmp_path):
    """Return a checkout with a configured build tree."""
    root = tmp_path / "lib"
    tree = root / "build"
    tree.mkdir(parents=True)
    (tree / "CMakeCache.txt").write_text(
        f"CMAKE_HOME_DIRECTORY:INTERNAL={root}\nCMAKE_BUILD_TYPE:STRING=Debug\n",
        encoding="utf-8")
    return root


def _install(checkout, prefix, runner=None, archive=False, force=False):
    """Run the installer; return its exit code, console and runner."""
    console, runner = RecordingConsole(), runner or _Runner()
    code = PackageInstaller(console, "cmake", runner, runner.capture).install(
        checkout, Path("build"), prefix, archive=archive, force=force)
    return code, console, runner


@pytest.mark.medium
def test_a_built_tree_is_installed_with_its_own_build_type(checkout):
    """Check the install command, its prefix and its config."""
    prefix = checkout / "out"
    code, _, runner = _install(checkout, prefix)
    assert code == 0
    assert runner.calls[0] == ["cmake", "--install", str(checkout / "build"), "--prefix",
                               str(prefix.resolve()), "--config", "Debug"]


@pytest.mark.medium
def test_an_install_writes_the_stage_marker_beside_the_files(checkout):
    """Check that the installed files and the stage marker are in the prefix."""
    prefix = checkout / "out"
    _install(checkout, prefix)
    assert (prefix / K_STAGE_MARKER).is_file() and (prefix / "installed.txt").is_file()


@pytest.mark.medium
def test_an_install_prints_one_line_counting_files_not_folders(checkout):
    """Check that cmake's lines are held back and one summary counts the file alone."""
    prefix = checkout / "out"
    _, console, _ = _install(checkout, prefix)
    assert _lines(console, "info") == [f"Installed 1 files, 0 up to date, into {prefix.resolve()}"]
    assert len(_lines(console, "command")) == 1


@pytest.mark.medium
def test_a_failed_install_prints_all_of_cmakes_output(checkout):
    """Check that a failure shows what cmake said and prints no summary."""
    code, console, _ = _install(checkout, checkout / "out", runner=_Runner(install_code=1))
    assert code == 1 and "CMake Error: file cannot create directory" in _lines(console, "error")[0]
    assert _lines(console, "info") == []


@pytest.mark.medium
def test_a_failed_install_leaves_no_stage_marker(checkout):
    """Check that a failed install writes no stage marker."""
    prefix = checkout / "out"
    _install(checkout, prefix, runner=_Runner(install_code=1))
    assert not (prefix / K_STAGE_MARKER).exists()


@pytest.mark.small
def test_the_summary_counts_up_to_date_files_apart():
    """Check that a kept file counts as up to date and a missing path counts as nothing."""
    prefix = Path("/prefix")
    output = f"-- Up-to-date: {prefix / 'a.hpp'}\n-- Installing: {prefix / 'gone.hpp'}\n"
    summary = install_summary(output, prefix, is_file=lambda path: path.name == "a.hpp")
    assert summary == f"Installed 0 files, 1 up to date, into {prefix}"


@pytest.mark.medium
def test_a_tree_that_is_not_built_exits_non_zero_naming_it(checkout):
    """Check that a folder with no cache is refused."""
    (checkout / "build" / "CMakeCache.txt").unlink()
    code, console, runner = _install(checkout, checkout / "out")
    assert code == 1 and "build" in _lines(console, "error")[0] and runner.calls == []


@pytest.mark.medium
def test_no_archive_runs_no_cpack(checkout):
    """Check that CPack does not run when the archive is not asked for."""
    _, _, without = _install(checkout, checkout / "a", archive=False)
    assert "cpack" not in [Path(command[0]).stem for command in without.calls]


@pytest.mark.medium
def test_an_archive_runs_cpack(checkout):
    """Check that CPack runs when the archive is asked for."""
    _, _, with_cpack = _install(checkout, checkout / "b", archive=True)
    assert "cpack" in [Path(command[0]).stem for command in with_cpack.calls]


@pytest.mark.medium
def test_a_prefix_with_foreign_files_needs_force(checkout):
    """Check that a folder this command did not stage is refused and named --force."""
    prefix = checkout / "out"
    prefix.mkdir()
    (prefix / "mine.txt").write_text("x")
    code, console, _ = _install(checkout, prefix)
    assert code == 1 and "--force" in _lines(console, "error")[0]


@pytest.mark.medium
def test_force_clears_a_prefix_with_foreign_files(checkout):
    """Check that --force empties a folder this command did not stage and installs."""
    prefix = checkout / "out"
    prefix.mkdir()
    (prefix / "mine.txt").write_text("x")
    code, _, _ = _install(checkout, prefix, force=True)
    assert code == 0 and not (prefix / "mine.txt").exists()


@pytest.mark.medium
def test_a_staged_prefix_is_emptied_without_force(checkout):
    """Check that a second run into the folder the first one staged needs no force."""
    prefix = checkout / "out"
    _install(checkout, prefix)
    (prefix / "stale.txt").write_text("x")
    assert _install(checkout, prefix)[0] == 0 and not (prefix / "stale.txt").exists()


@pytest.mark.medium
def test_the_prefix_is_never_the_checkout(checkout):
    """Check that the checkout itself is refused even with force."""
    code, console, runner = _install(checkout, checkout, force=True)
    assert code == 1 and "checkout" in _lines(console, "error")[0] and runner.calls == []
