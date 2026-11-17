# test_glob_search.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the tool globs and candidate-path lookups."""

from __future__ import annotations

import pytest

from sushicore.provision.glob_search import first_existing, first_glob_match


@pytest.mark.medium
def test_first_glob_match_takes_the_highest_sorting_hit_of_the_first_pattern(tmp_path):
    """Check that the latest version of the first pattern with hits is returned."""
    for version in ("1.0", "2.0"):
        (tmp_path / version).mkdir()
    pattern = str(tmp_path / "*")
    assert first_glob_match([str(tmp_path / "none-*"), pattern]) == str(tmp_path / "2.0")


@pytest.mark.small
def test_first_glob_match_is_empty_without_a_hit():
    """Check that patterns with no hit give an empty string."""
    assert first_glob_match(["/no-such-folder-xyz/*"]) == ""


@pytest.mark.medium
def test_first_existing_returns_the_first_path_that_exists(tmp_path):
    """Check that a missing candidate is skipped and the next existing one is returned."""
    present = tmp_path / "present"
    present.write_text("")
    assert first_existing([str(tmp_path / "absent"), str(present)]) == str(present)


@pytest.mark.small
def test_first_existing_is_empty_when_none_exist():
    """Check that no existing candidate gives an empty string."""
    assert first_existing(["/no-such-file-xyz"]) == ""
