# test_vs_locator.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the Visual Studio script finder."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.proc_memory import RecordingRunner
from sushicore.provision import vs_locator
from sushicore.provision.host import PosixHost, WindowsHost
from sushicore.provision.vs_locator import find_vcvars


@pytest.mark.small
def test_find_vcvars_is_none_off_windows():
    """Check that no Visual Studio script is looked for off Windows."""
    assert find_vcvars(host=PosixHost(), vswhere=lambda: Path("never")) is None


def _vs_tree(root, year, edition):
    """Create a vcvars64.bat of *year* and *edition* below *root* and return it."""
    bat = root / "Microsoft Visual Studio" / year / edition / "VC" / "Auxiliary" / "Build"
    bat.mkdir(parents=True)
    (bat / "vcvars64.bat").write_text("")
    return bat / "vcvars64.bat"


@pytest.mark.medium
def test_find_vcvars_scans_the_newest_year_first(tmp_path):
    """Check that the disk scan takes the newest year's install."""
    _vs_tree(tmp_path, "2019", "Community")
    newest = _vs_tree(tmp_path, "2026", "BuildTools")
    found = find_vcvars(host=WindowsHost(), vswhere=lambda: None, program_files=[tmp_path])
    assert found == newest


@pytest.mark.small
def test_find_vcvars_prefers_vswhere():
    """Check that the install vswhere reports wins over the disk scan."""
    hit = Path("/machine/vcvars64.bat")
    assert find_vcvars(host=WindowsHost(), vswhere=lambda: hit, program_files=[]) == hit


@pytest.mark.small
def test_find_vcvars_is_none_when_nothing_is_installed():
    """Check that no vswhere answer and no scanned folder give None."""
    assert find_vcvars(host=WindowsHost(), vswhere=lambda: None, program_files=[]) is None


def _fake_vswhere(tmp_path):
    """Put a vswhere.exe file where the finder looks and return the folder holding it."""
    vswhere = tmp_path / "Microsoft Visual Studio" / "Installer" / "vswhere.exe"
    vswhere.parent.mkdir(parents=True)
    vswhere.write_text("")
    return tmp_path


@pytest.mark.medium
@pytest.mark.parametrize(("runner", "logged"), [
    (RecordingRunner(RecordingConsole()).script_missing(), "vswhere did not run (Executable not found"),
    (RecordingRunner(RecordingConsole()).script(3), "vswhere exited with status 3"),
], ids=["did not run", "exited non-zero"])
def test_find_vcvars_logs_a_vswhere_that_failed(tmp_path, caplog, runner, logged):
    """Check that a vswhere that cannot start or exits non-zero is recorded and finds nothing."""
    program_files = str(_fake_vswhere(tmp_path))
    with caplog.at_level("WARNING", logger=vs_locator.__name__):
        found = find_vcvars(
            host=WindowsHost(),
            vswhere=lambda: vs_locator.vcvars_from_vswhere(program_files, runner),
            program_files=[])
    assert found is None
    assert logged in caplog.text
