# test_package_install.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests for the install and archive step of the shared package command."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.provision.package_install import (K_STAGE_MARKER, CapturedRun,
                                                  PackageInstaller, install_summary)

pytestmark = pytest.mark.medium


class _Console:
    """Collects the error, command and information lines."""

    def __init__(self) -> None:
        """Start empty."""
        self.errors: list[str] = []
        self.commands: list[str] = []
        self.infos: list[str] = []

    def error(self, text: str) -> None:
        """Keep an error line."""
        self.errors.append(text)

    def command(self, text: str) -> None:
        """Keep a command line."""
        self.commands.append(text)

    def info(self, text: str) -> None:
        """Keep an information line."""
        self.infos.append(text)


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
    console, runner = _Console(), runner or _Runner()
    code = PackageInstaller(console, "cmake", runner, runner.capture).install(
        checkout, Path("build"), prefix, archive=archive, force=force)
    return code, console, runner


def test_a_built_tree_is_installed_with_its_own_build_type(checkout):
    """Check the install command, its prefix and its config, and the stage marker."""
    prefix = checkout / "out"
    code, _, runner = _install(checkout, prefix)
    assert code == 0
    assert runner.calls[0] == ["cmake", "--install", str(checkout / "build"), "--prefix",
                               str(prefix.resolve()), "--config", "Debug"]
    assert (prefix / K_STAGE_MARKER).is_file() and (prefix / "installed.txt").is_file()


def test_an_install_prints_one_line_counting_files_not_folders(checkout):
    """Check that cmake's lines are held back and one summary counts the file alone."""
    prefix = checkout / "out"
    _, console, _ = _install(checkout, prefix)
    assert console.infos == [f"Installed 1 files, 0 up to date, into {prefix.resolve()}"]
    assert len(console.commands) == 1


def test_a_failed_install_prints_all_of_cmakes_output(checkout):
    """Check that a failure shows what cmake said and leaves no stage marker."""
    prefix = checkout / "out"
    code, console, _ = _install(checkout, prefix, runner=_Runner(install_code=1))
    assert code == 1 and "CMake Error: file cannot create directory" in console.errors[0]
    assert console.infos == [] and not (prefix / K_STAGE_MARKER).exists()


def test_the_summary_counts_up_to_date_files_apart(tmp_path):
    """Check that a kept file counts as up to date and a missing path counts as nothing."""
    (tmp_path / "a.hpp").write_text("x")
    output = f"-- Up-to-date: {tmp_path / 'a.hpp'}\n-- Installing: {tmp_path / 'gone.hpp'}\n"
    assert install_summary(output, tmp_path) == f"Installed 0 files, 1 up to date, into {tmp_path}"


def test_a_tree_that_is_not_built_exits_non_zero_naming_it(checkout):
    """Check that a folder with no cache is refused."""
    (checkout / "build" / "CMakeCache.txt").unlink()
    code, console, runner = _install(checkout, checkout / "out")
    assert code == 1 and "build" in console.errors[0] and runner.calls == []


def test_no_archive_runs_no_cpack_and_archive_does(checkout):
    """Check that CPack runs only when the archive is asked for."""
    _, _, without = _install(checkout, checkout / "a", archive=False)
    _, _, with_cpack = _install(checkout, checkout / "b", archive=True)
    assert len(without.calls) == 1
    assert Path(with_cpack.calls[1][0]).stem == "cpack"


def test_a_prefix_with_foreign_files_needs_force(checkout):
    """Check that a folder this command did not stage is refused, and cleared with force."""
    prefix = checkout / "out"
    prefix.mkdir()
    (prefix / "mine.txt").write_text("x")
    code, console, _ = _install(checkout, prefix)
    assert code == 1 and "--force" in console.errors[0]
    code, _, _ = _install(checkout, prefix, force=True)
    assert code == 0 and not (prefix / "mine.txt").exists()


def test_a_staged_prefix_is_emptied_without_force(checkout):
    """Check that a second run into the folder the first one staged needs no force."""
    prefix = checkout / "out"
    _install(checkout, prefix)
    (prefix / "stale.txt").write_text("x")
    assert _install(checkout, prefix)[0] == 0 and not (prefix / "stale.txt").exists()


def test_the_prefix_is_never_the_checkout(checkout):
    """Check that the checkout itself is refused even with force."""
    code, console, runner = _install(checkout, checkout, force=True)
    assert code == 1 and "checkout" in console.errors[0] and runner.calls == []
