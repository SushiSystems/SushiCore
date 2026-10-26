# test_package_install.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests for the install and archive step of the shared package command."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.provision.package_install import K_STAGE_MARKER, PackageInstaller

pytestmark = pytest.mark.medium


class _Console:
    """Collects the error and command lines."""

    def __init__(self) -> None:
        """Start empty."""
        self.errors: list[str] = []
        self.commands: list[str] = []

    def error(self, text: str) -> None:
        """Keep an error line."""
        self.errors.append(text)

    def command(self, text: str) -> None:
        """Keep a command line."""
        self.commands.append(text)


class _Runner:
    """Records commands and installs a file the way cmake --install would."""

    def __init__(self) -> None:
        """Start with no calls."""
        self.calls: list[list[str]] = []

    def __call__(self, command, cwd, env=None) -> int:
        """Record *command*; write a file into the prefix on an install."""
        self.calls.append(command)
        if "--install" in command:
            Path(command[command.index("--prefix") + 1], "installed.txt").write_text("x")
        return 0


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
    code = PackageInstaller(console, "cmake", runner).install(
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
