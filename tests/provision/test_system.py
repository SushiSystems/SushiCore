# test_system.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the system helpers: os-release, sudo and the oneAPI repository."""

from __future__ import annotations

import pytest

from sushicore.provision import system


def _refusing(error: OSError):
    """Return a reader that raises *error* in place of reading the file."""
    def read_text() -> str:
        """Raise the configured error."""
        raise error
    return read_text


def _system_warnings(caplog) -> list[str]:
    """Return the warnings the provision logger recorded."""
    return [r.getMessage() for r in caplog.records
            if r.name.startswith("sushicore.provision") and r.levelname == "WARNING"]


@pytest.mark.small
def test_sudo_bash_dry_run_shows_the_command_and_runs_nothing(recording_console):
    """Check that a dry run of sudo_bash shows the command, says it was not executed and answers True."""
    assert system.sudo_bash("false", dry_run=True) is True
    assert [(name, args[0]) for name, args in recording_console.calls] == [
        ("command", "false"), ("info", "(dry-run) not executed")]


@pytest.mark.small
def test_os_release_parses_its_keys():
    """Check that os_release reads key=value lines, drops quotes and skips comments."""
    text = '# comment\nID=ubuntu\nVERSION_ID="24.04"\n'
    assert system.os_release(lambda: text) == {"ID": "ubuntu", "VERSION_ID": "24.04"}


@pytest.mark.small
def test_an_unreadable_os_release_is_recorded(caplog):
    """Check that an os-release that cannot be read yields no fields and one warning."""
    with caplog.at_level("WARNING", logger="sushicore.provision"):
        assert system.os_release(_refusing(PermissionError(13, "Permission denied"))) == {}
    assert len(_system_warnings(caplog)) == 1
    assert "/etc/os-release" in _system_warnings(caplog)[0]


@pytest.mark.small
def test_an_absent_os_release_is_not_a_warning(caplog):
    """Check that a machine with no os-release file yields no fields and no warning."""
    with caplog.at_level("WARNING", logger="sushicore.provision"):
        assert system.os_release(_refusing(FileNotFoundError(2, "No such file"))) == {}
    assert _system_warnings(caplog) == []


@pytest.mark.medium
def test_a_dry_run_of_the_oneapi_repository_succeeds_without_an_error(recording_console):
    """Check that a dry run answers True and records no error line."""
    assert system.ensure_intel_oneapi_repo(True) is True
    assert not [name for name, _ in recording_console.calls if name == "error"]
