# test_user_environment.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests for the user's persistent environment variables."""

from __future__ import annotations

import pytest

from sushicore.provision import user_environment
from sushicore.provision.user_environment import (
    BLOCK_BEGIN,
    BLOCK_END,
    ProfileEnvironment,
    RegistryEnvironment,
    read_user_variable,
    remove_user_variable,
    write_user_variable,
)


class FakeKey:
    """Stands in for the opened registry key, over a dict the test owns."""

    def __init__(self, values: dict[str, str], log: list[str]) -> None:
        """Share *values* and *log* with the test."""
        self._values = values
        self._log = log

    def query(self, name: str) -> str | None:
        """Return the value stored under *name*."""
        return self._values.get(name)

    def set(self, name: str, value: str) -> None:
        """Store *value* under *name*."""
        self._values[name] = value

    def delete(self, name: str) -> None:
        """Delete *name* when it is there."""
        self._values.pop(name, None)

    def close(self) -> None:
        """Record that the key was released."""
        self._log.append("close")


@pytest.fixture
def registry():
    """Return a registry store over a fake key, its values and its event log."""
    values: dict[str, str] = {}
    log: list[str] = []
    store = RegistryEnvironment(
        open_key=lambda: FakeKey(values, log),
        broadcast=lambda: log.append("broadcast"),
    )
    return store, values, log


def test_registry_write_stores_the_value_and_broadcasts(registry):
    """Check that a registry write stores the value, closes the key and broadcasts."""
    store, values, log = registry
    write_user_variable("SUSHISYSTEMS_HOME", "D:/deps", store)
    assert values == {"SUSHISYSTEMS_HOME": "D:/deps"}
    assert log == ["close", "broadcast"]


def test_registry_read_returns_none_for_an_unset_name(registry):
    """Check that a registry read of an unset name returns None without a broadcast."""
    store, _values, log = registry
    assert read_user_variable("SUSHISYSTEMS_HOME", store) is None
    assert log == ["close"]


def test_registry_read_returns_what_was_written(registry):
    """Check that a registry read returns the value a write stored."""
    store, _values, _log = registry
    write_user_variable("SUSHISYSTEMS_HOME", "D:/deps", store)
    assert read_user_variable("SUSHISYSTEMS_HOME", store) == "D:/deps"


def test_registry_remove_deletes_the_value_and_broadcasts(registry):
    """Check that a registry remove deletes the value and broadcasts."""
    store, values, log = registry
    values["SUSHISYSTEMS_HOME"] = "D:/deps"
    remove_user_variable("SUSHISYSTEMS_HOME", store)
    assert values == {}
    assert log == ["close", "broadcast"]


def test_registry_remove_of_an_unset_name_is_not_an_error(registry):
    """Check that removing a name the registry does not hold raises nothing."""
    store, values, _log = registry
    remove_user_variable("SUSHISYSTEMS_HOME", store)
    assert values == {}


def test_profile_write_creates_the_block(tmp_path):
    """Check that the first write creates the file with one marked block."""
    profile = tmp_path / ".profile"
    write_user_variable("SUSHISYSTEMS_HOME", "/opt/deps", ProfileEnvironment(profile))
    assert profile.read_text(encoding="utf-8") == (
        f'{BLOCK_BEGIN}\nexport SUSHISYSTEMS_HOME="/opt/deps"\n{BLOCK_END}\n'
    )


def test_profile_write_keeps_the_lines_around_the_block(tmp_path):
    """Check that a write leaves the user's own lines before and after the block."""
    profile = tmp_path / ".profile"
    profile.write_text(
        f'export PATH="$HOME/bin:$PATH"\n{BLOCK_BEGIN}\nexport A="1"\n{BLOCK_END}\n'
        'alias ll="ls -l"\n',
        encoding="utf-8",
    )
    ProfileEnvironment(profile).write("B", "2")
    assert profile.read_text(encoding="utf-8") == (
        f'export PATH="$HOME/bin:$PATH"\n{BLOCK_BEGIN}\nexport A="1"\nexport B="2"\n'
        f'{BLOCK_END}\nalias ll="ls -l"\n'
    )


def test_profile_write_replaces_the_line_of_a_set_name(tmp_path):
    """Check that a second write replaces the variable's line in place."""
    store = ProfileEnvironment(tmp_path / ".profile")
    store.write("A", "1")
    store.write("B", "2")
    store.write("A", "3")
    text = (tmp_path / ".profile").read_text(encoding="utf-8")
    assert text == f'{BLOCK_BEGIN}\nexport A="3"\nexport B="2"\n{BLOCK_END}\n'


def test_profile_read_returns_what_was_written(tmp_path):
    """Check that a value with quotes, dollars and backslashes reads back unchanged."""
    store = ProfileEnvironment(tmp_path / ".profile")
    value = 'C:\\deps "x" $HOME `id`'
    store.write("A", value)
    assert read_user_variable("A", store) == value
    assert '\\$HOME' in (tmp_path / ".profile").read_text(encoding="utf-8")


def test_profile_read_returns_none_without_a_file(tmp_path):
    """Check that a read from a missing file returns None and creates nothing."""
    profile = tmp_path / ".profile"
    assert read_user_variable("A", ProfileEnvironment(profile)) is None
    assert not profile.exists()


def test_profile_read_ignores_an_export_outside_the_block(tmp_path):
    """Check that a line the user wrote outside the block is not read as stored."""
    profile = tmp_path / ".profile"
    profile.write_text('export A="mine"\n', encoding="utf-8")
    assert ProfileEnvironment(profile).read("A") is None


def test_profile_remove_deletes_one_line(tmp_path):
    """Check that a remove deletes the variable's line and keeps the others."""
    store = ProfileEnvironment(tmp_path / ".profile")
    store.write("A", "1")
    store.write("B", "2")
    remove_user_variable("A", store)
    text = (tmp_path / ".profile").read_text(encoding="utf-8")
    assert text == f'{BLOCK_BEGIN}\nexport B="2"\n{BLOCK_END}\n'


def test_profile_remove_of_the_last_variable_drops_the_markers(tmp_path):
    """Check that an emptied block leaves the file as it was before the write."""
    profile = tmp_path / ".profile"
    original = 'export PATH="$HOME/bin:$PATH"\n'
    profile.write_text(original, encoding="utf-8")
    store = ProfileEnvironment(profile)
    store.write("A", "1")
    store.remove("A")
    assert profile.read_text(encoding="utf-8") == original


def test_profile_remove_of_an_unset_name_leaves_the_file_alone(tmp_path):
    """Check that removing a name the block does not hold writes nothing."""
    profile = tmp_path / ".profile"
    ProfileEnvironment(profile).remove("A")
    assert not profile.exists()


def test_default_store_is_used_when_none_is_passed(tmp_path, monkeypatch):
    """Check that the three functions fall back to the platform's store."""
    store = ProfileEnvironment(tmp_path / ".profile")
    monkeypatch.setattr(user_environment, "default_environment", lambda: store)
    write_user_variable("A", "1")
    assert read_user_variable("A") == "1"
    remove_user_variable("A")
    assert read_user_variable("A") is None
