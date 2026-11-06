# test_level_zero.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the Level Zero backend spec and its loader locator."""

from __future__ import annotations

import pathlib
from types import SimpleNamespace

import pytest

from sushicore.provision.gpu.backend import ToolkitInstall
from sushicore.provision.gpu.level_zero import LinuxLevelZeroLocator

_CFG = SimpleNamespace(platform="linux")

_APT_SUFFIX = ("apt-get install -y level-zero intel-oneapi-runtime-opencl "
               "intel-oneapi-runtime-libs")


class _Steps:
    """Records each shell line it is asked to run and answers a fixed outcome."""

    def __init__(self, succeeds: bool = True) -> None:
        """Start with no recorded lines."""
        self.lines: list[tuple[str, bool]] = []
        self._succeeds = succeeds

    def __call__(self, line: str, dry_run: bool) -> bool:
        """Record *line* and return the fixed outcome."""
        self.lines.append((line, dry_run))
        return self._succeeds


@pytest.mark.small
@pytest.mark.parametrize(("superuser", "sudo"), [(False, "sudo "), (True, "")],
                         ids=["user", "root"])
def test_level_zero_linux_provision_installs_with_sudo_unless_root(superuser, sudo):
    """Check that the apt line carries sudo for a user and none for root."""
    steps = _Steps()
    locator = LinuxLevelZeroLocator(ensure_repo=lambda dry_run: True,
                                    is_superuser=lambda: superuser, run_steps=steps)

    assert locator.provision(_CFG, dry_run=True) is True

    assert steps.lines == [(f"{sudo}apt-get update && {sudo}{_APT_SUFFIX}", True)]


@pytest.mark.small
def test_level_zero_linux_provision_stops_when_the_repository_is_not_ready():
    """Check that a failed repository setup returns False and runs no apt line."""
    steps = _Steps()
    locator = LinuxLevelZeroLocator(ensure_repo=lambda dry_run: False,
                                    is_superuser=lambda: False, run_steps=steps)

    assert locator.provision(_CFG, dry_run=False) is False

    assert steps.lines == []


@pytest.mark.small
def test_level_zero_linux_provision_warns_when_the_install_fails(recording_console):
    """Check that a failed apt line returns False and says the build falls back."""
    locator = LinuxLevelZeroLocator(ensure_repo=lambda dry_run: True,
                                    is_superuser=lambda: False, run_steps=_Steps(False))

    assert locator.provision(_CFG, dry_run=False) is False

    assert recording_console.texts("warn") == [
        "Intel GPU runtime install failed; the build will fall back to the CPU/OpenCL path."]


@pytest.mark.small
def test_level_zero_locator_takes_the_directory_find_library_names():
    """Check that the folder of the path the library lookup returns is the root."""
    locator = LinuxLevelZeroLocator(
        find_library=lambda name: "/usr/lib/x86_64-linux-gnu/libze_loader.so.1", lib_dirs=())

    assert locator.locate(_CFG) == ToolkitInstall(
        root=pathlib.Path("/usr/lib/x86_64-linux-gnu"), version=None)


@pytest.mark.medium
def test_level_zero_locator_falls_back_to_the_known_lib_dirs(tmp_path):
    """Check that a directory holding the loader is found when the lookup finds nothing."""
    (tmp_path / "libze_loader.so.1").write_text("")
    locator = LinuxLevelZeroLocator(find_library=lambda name: None, lib_dirs=[str(tmp_path)])

    assert locator.locate(_CFG) == ToolkitInstall(root=tmp_path, version=None)


@pytest.mark.medium
def test_level_zero_locator_reports_nothing_when_the_loader_is_absent(tmp_path):
    """Check that no loader in any directory gives no install."""
    locator = LinuxLevelZeroLocator(find_library=lambda name: None, lib_dirs=[str(tmp_path)])

    assert locator.locate(_CFG) is None
