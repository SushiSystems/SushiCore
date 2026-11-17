# test_current.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the choice between the targets."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from sushicore.provision.target import LinuxTarget, WindowsTarget, target_for_platform, target_of


@pytest.mark.small
@pytest.mark.parametrize(("platform", "expected"), [
    ("windows", WindowsTarget), ("linux", LinuxTarget), ("darwin", LinuxTarget)])
def test_target_for_platform_names_windows_and_falls_back_to_linux(platform, expected):
    """Check that only the name windows selects the Windows target."""
    assert type(target_for_platform(platform)) is expected


@pytest.mark.small
def test_target_of_follows_the_platform_of_the_config():
    """Check that the target of a config is the one its platform names."""
    assert target_of(SimpleNamespace(platform="windows")).name == "windows"
