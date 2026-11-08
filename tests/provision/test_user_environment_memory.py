# test_user_environment_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What the in-memory environment key promises: it holds values in the dict it was given."""

from __future__ import annotations

import pytest

from sushicore.provision.user_environment_memory import InMemoryEnvironmentKey


@pytest.mark.small
def test_a_stored_value_is_queried_and_a_deleted_one_is_gone():
    """Check that set then query gives the value and delete then query gives None."""
    values: dict[str, str] = {}
    key = InMemoryEnvironmentKey(values, [])
    key.set("A", "1")
    stored = key.query("A")
    key.delete("A")
    assert (stored, key.query("A"), values) == ("1", None, {})


@pytest.mark.small
def test_deleting_an_absent_name_raises_nothing():
    """Check that deleting a name the key does not hold is not an error."""
    InMemoryEnvironmentKey({}, []).delete("A")


@pytest.mark.small
def test_closing_the_key_is_logged():
    """Check that close appends one close entry to the shared log."""
    log: list[str] = []
    InMemoryEnvironmentKey({}, log).close()
    assert log == ["close"]
