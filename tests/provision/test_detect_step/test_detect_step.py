# test_detect_step.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What the detect step tells the user about a missing component and the removal of the install."""

from __future__ import annotations

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.provision.config import ProvisionSettings
from sushicore.provision.detect_step import DetectStep, removal_note
from sushicore.provision.fragments_memory import InMemoryDependencySource
from sushicore.provision.pipeline import InstallContext


def _context(**overrides) -> InstallContext:
    """Build an install context for a Linux run with *overrides* applied."""
    return InstallContext(cfg=ProvisionSettings(platform="linux"), **overrides)


def _rerun_hint(ctx: InstallContext) -> str:
    """Report an inventory with one missing component through *ctx*; return everything printed."""
    out = RecordingConsole()
    rows = [("ninja", "MISSING", "shared", "not found")]
    DetectStep(InMemoryDependencySource([]), console=out).report_inventory(ctx, rows)
    return "\n".join(out.texts("info"))


@pytest.mark.small
def test_missing_dependency_hint_names_the_calling_program():
    """Assert the re-run hint names the program in the context, not hub."""
    hint = _rerun_hint(_context(program="st"))
    assert "`st setup`" in hint
    assert "hub install" not in hint


@pytest.mark.small
def test_missing_dependency_hint_uses_the_rerun_command_the_consumer_names():
    """Assert a consumer that names its own re-run command is quoted, whatever its program is called."""
    assert "`hub install`" in _rerun_hint(_context(program="hub", rerun_command="hub install"))


@pytest.mark.small
def test_a_context_names_no_consumer_until_it_is_given_one():
    """Assert the shared code carries no default consumer: with no program the hint is the bare setup."""
    hint = _rerun_hint(_context())
    assert "hub" not in hint
    assert "`setup`" in hint


@pytest.mark.small
@pytest.mark.parametrize(("hint", "expected"), [
    ("(`hub remove --all` does it for you).",
     "Remove the whole install by deleting that folder. (`hub remove --all` does it for you)."),
    ("", "Remove the whole install by deleting that folder."),
])
def test_the_removal_note_ends_with_the_hint_the_consumer_supplies_or_stands_alone(hint, expected):
    """Check that removal_note appends the consumer's hint, and leaves the plain note without one."""
    assert removal_note(_context(program="hub", removal_hint=hint)) == expected
