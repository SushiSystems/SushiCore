# test_system.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026 Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests for the OS helpers."""

from __future__ import annotations

from sushicore.provision import system


def test_sudo_bash_dry_run_runs_nothing(recording_console):
    """Check that a dry run of sudo_bash runs nothing."""
    assert system.sudo_bash("false", dry_run=True) is True


def test_os_release_is_a_dict():
    """Check that os_release returns a dict."""
    assert isinstance(system.os_release(), dict)



def _os_release_raising(monkeypatch, error: OSError) -> None:
    """Make reading /etc/os-release raise *error*."""
    class _File:
        """Stands in for the os-release path."""

        def __init__(self, path: str) -> None:
            """Accept the path the reader opens."""

        def read_text(self, encoding: str | None = None) -> str:
            """Raise the configured error in place of reading."""
            raise error

    monkeypatch.setattr(system, "Path", _File)


def _system_warnings(caplog) -> list[str]:
    """Return the warnings the provision logger recorded."""
    return [r.getMessage() for r in caplog.records
            if r.name == "sushicore.provision" and r.levelname == "WARNING"]


def test_an_unreadable_os_release_is_recorded(monkeypatch, caplog):
    """Check that an os-release that cannot be read yields no fields and one warning."""
    _os_release_raising(monkeypatch, PermissionError(13, "Permission denied"))
    with caplog.at_level("WARNING", logger="sushicore.provision"):
        assert system.os_release() == {}
    assert len(_system_warnings(caplog)) == 1
    assert "/etc/os-release" in _system_warnings(caplog)[0]


def test_an_absent_os_release_is_not_a_warning(monkeypatch, caplog):
    """Check that a machine with no os-release file yields no fields and no warning."""
    _os_release_raising(monkeypatch, FileNotFoundError(2, "No such file"))
    with caplog.at_level("WARNING", logger="sushicore.provision"):
        assert system.os_release() == {}
    assert _system_warnings(caplog) == []
