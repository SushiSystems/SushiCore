# test_settings_reads.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the search for settings the shared tools read that a repository lacks."""

from __future__ import annotations

import pytest

from sushicore.shared_tools.errors import SharedToolsError
from sushicore.shared_tools.settings_reads import missing_settings

pytestmark = pytest.mark.small

K_TOOL = 'x = getattr(settings, "K_ONE", 1)\ny = settings.K_TWO\nz = settings.K_HELD\n'
K_CORE = "K_ONE: int = 7\nK_TWO = ('a', 'b')\nK_HELD = 0\n"


def test_each_setting_read_and_not_held_is_named_with_the_core_value() -> None:
    """Both read forms are found, and each name carries the value text of SushiCore."""
    found = missing_settings([K_TOOL], "K_HELD = 5\n", K_CORE)
    assert found == {"K_ONE": "7", "K_TWO": "('a', 'b')"}


def test_a_setting_the_core_lacks_too_has_no_value() -> None:
    """A name SushiCore does not define is still named, with None."""
    assert missing_settings(['settings.K_GONE\n'], "", K_CORE) == {"K_GONE": None}


def test_a_target_without_a_settings_file_lacks_every_setting() -> None:
    """None for the target means every read setting is missing."""
    assert list(missing_settings([K_TOOL], None, K_CORE)) == ["K_HELD", "K_ONE", "K_TWO"]


def test_a_settings_file_that_is_not_python_is_refused() -> None:
    """A syntax error raises the module's error, not a bare SyntaxError."""
    with pytest.raises(SharedToolsError):
        missing_settings([K_TOOL], "K_ = = 1\n", K_CORE)
