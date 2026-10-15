# test_errors.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests the errors a Sushi CLI reports to its user."""

from pathlib import Path

import pytest

from sushicore.errors import ConfigError, DigestMismatchError, SushiCoreError

pytestmark = pytest.mark.small


def test_a_config_error_is_a_sushicore_error_and_a_value_error():
    error = ConfigError("bad value")
    assert isinstance(error, SushiCoreError)
    assert isinstance(error, ValueError)


def test_a_digest_mismatch_names_the_file_and_both_digests():
    error = DigestMismatchError(Path("tool.zip"), expected="aa", actual="bb")
    assert (error.path, error.expected, error.actual) == (Path("tool.zip"), "aa", "bb")
    assert "tool.zip" in str(error)
    assert "bb" in str(error) and "pins aa" in str(error)
