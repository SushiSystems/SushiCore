# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the OS helpers."""

from __future__ import annotations

from sushicore.provision import system


def test_sudo_bash_dry_run_runs_nothing(recording_console):
    """Check that a dry run of sudo_bash runs nothing."""
    assert system.sudo_bash("false", dry_run=True) is True


def test_os_release_is_a_dict():
    """Check that os_release returns a dict."""
    assert isinstance(system.os_release(), dict)
