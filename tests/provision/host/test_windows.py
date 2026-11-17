# test_windows.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the Windows host."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.proc_memory import RecordingRunner
from sushicore.provision.host import WindowsHost


@pytest.mark.small
def test_the_windows_host_states_its_conventions():
    """Check the compiler name, index key, prefix search, Visual Studio and registry answers."""
    host = WindowsHost()

    assert (host.nvcc_name, host.cuda_platform_key) == ("nvcc.exe", "windows-x86_64")
    assert (host.searches_system_prefixes, host.hosts_visual_studio,
            host.keeps_environment_in_registry) == (False, True, True)


@pytest.mark.small
def test_the_windows_host_prefixes_a_path_once():
    """Check that the extended-length prefix is added to a path once, and never doubled."""
    host = WindowsHost()
    once = host.long_path(Path("a"))

    assert str(once).startswith("\\" * 2 + "?" + "\\")
    assert host.long_path(once) == once


def _runner() -> RecordingRunner:
    """Return a runner that records commands and starts no process."""
    return RecordingRunner(RecordingConsole())


@pytest.mark.small
def test_a_video_controller_query_that_times_out_is_recorded(caplog):
    """Check that a PowerShell query that times out yields no adapters and one warning."""
    with caplog.at_level("WARNING", logger="sushicore.provision"):
        assert WindowsHost().display_adapters(_runner().script_timeout()) == ""
    warnings = [r.getMessage() for r in caplog.records if r.levelname == "WARNING"]
    assert len(warnings) == 1
    assert "timed out" in warnings[0]


@pytest.mark.small
def test_the_video_controller_names_come_back_in_lower_case():
    """Check that the PowerShell output is lower-cased."""
    assert WindowsHost().display_adapters(_runner().script(0, ("NVIDIA GeForce",))) == (
        "nvidia geforce\n")
