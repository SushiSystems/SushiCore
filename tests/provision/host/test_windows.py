# test_windows.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the Windows host."""

from __future__ import annotations

from pathlib import Path

import pytest

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
