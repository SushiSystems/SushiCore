# test_deprecated_name.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the warning every restored name raises."""

from __future__ import annotations

import warnings

import pytest

from sushicore.deprecated_name import warn_deprecated

pytestmark = pytest.mark.small


def _old_function() -> None:
    """Stand in for a restored function."""
    warn_deprecated("old_function", "new_function")


def test_the_warning_names_the_old_name_and_its_replacement():
    """Check that the message carries both names."""
    with pytest.warns(DeprecationWarning) as caught:
        _old_function()
    assert str(caught[0].message) == "old_function is deprecated; use new_function"


def test_the_warning_points_at_the_caller_of_the_deprecated_function():
    """Check that the reported file is this one, not the module that raised the warning."""
    with pytest.warns(DeprecationWarning) as caught:
        _old_function()
    assert caught[0].filename == __file__


def test_the_warning_is_a_deprecation_warning_that_an_error_filter_can_raise():
    """Check that the category is DeprecationWarning, so a consumer can turn it into an error."""
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        with pytest.raises(DeprecationWarning):
            _old_function()
