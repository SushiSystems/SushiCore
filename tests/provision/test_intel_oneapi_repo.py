# test_intel_oneapi_repo.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the Intel oneAPI apt repository setup."""

from __future__ import annotations

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.proc_memory import RecordingRunner
from sushicore.provision.intel_oneapi_repo import ensure_intel_oneapi_repo


@pytest.mark.small
def test_a_dry_run_of_the_oneapi_repository_succeeds_without_an_error(recording_console, tmp_path):
    """Check that a dry run answers True and records no error line."""
    assert ensure_intel_oneapi_repo(True, console=recording_console,
                                    keyring=tmp_path / "absent.gpg") is True
    assert not [name for name, _ in recording_console.calls if name == "error"]


@pytest.mark.small
def test_a_failed_oneapi_repository_step_is_one_error(recording_console, tmp_path):
    """Check that a bash step that exits non-zero reports one error and answers False."""
    runner = RecordingRunner(RecordingConsole()).script(1)
    assert ensure_intel_oneapi_repo(False, runner, console=recording_console,
                                    keyring=tmp_path / "absent.gpg") is False
    assert [name for name, _ in recording_console.calls].count("error") == 1
    assert len(runner.commands) == 1


@pytest.mark.small
def test_a_configured_repository_is_left_alone(recording_console, tmp_path):
    """Check that existing keyring and source list files end the setup with no command run."""
    keyring = tmp_path / "keyring.gpg"
    source_list = tmp_path / "oneAPI.list"
    keyring.write_text("")
    source_list.write_text("")
    runner = RecordingRunner(RecordingConsole())
    assert ensure_intel_oneapi_repo(False, runner, console=recording_console,
                                    keyring=keyring, source_list=source_list) is True
    assert runner.commands == []
