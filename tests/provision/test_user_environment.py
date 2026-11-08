# test_user_environment.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the user's persistent environment variables."""

from __future__ import annotations

import pytest

from sushicore.provision.user_environment import (
    BLOCK_BEGIN,
    BLOCK_END,
    ProfileEnvironment,
    RegistryEnvironment,
    default_environment,
    read_user_variable,
    remove_user_variable,
    write_user_variable,
)
from sushicore.provision.user_environment_memory import InMemoryEnvironmentKey


class UserEnvironmentContract:
    """The promises every user environment store keeps; a subclass supplies the store."""

    def test_an_unset_name_reads_as_none(self, store):
        assert read_user_variable("SUSHISYSTEMS_HOME", store) is None

    def test_a_read_returns_what_was_written(self, store):
        write_user_variable("SUSHISYSTEMS_HOME", "D:/deps", store)
        assert read_user_variable("SUSHISYSTEMS_HOME", store) == "D:/deps"

    def test_a_remove_unsets_the_name(self, store):
        write_user_variable("SUSHISYSTEMS_HOME", "D:/deps", store)
        remove_user_variable("SUSHISYSTEMS_HOME", store)
        assert read_user_variable("SUSHISYSTEMS_HOME", store) is None

    def test_removing_an_unset_name_is_not_an_error(self, store):
        remove_user_variable("SUSHISYSTEMS_HOME", store)
        assert read_user_variable("SUSHISYSTEMS_HOME", store) is None


def _registry():
    """Return a registry store over an in-memory key, with the key's values and the event log."""
    values: dict[str, str] = {}
    log: list[str] = []
    store = RegistryEnvironment(
        open_key=lambda: InMemoryEnvironmentKey(values, log),
        broadcast=lambda: log.append("broadcast"),
    )
    return store, values, log


@pytest.mark.small
class TestRegistryEnvironmentKeepsTheUserEnvironmentContract(UserEnvironmentContract):
    """The registry store, over an in-memory key."""

    @pytest.fixture
    def store(self):
        return _registry()[0]


@pytest.mark.medium
class TestProfileEnvironmentKeepsTheUserEnvironmentContract(UserEnvironmentContract):
    """The profile store, over a file in the test's folder."""

    @pytest.fixture
    def store(self, tmp_path):
        return ProfileEnvironment(tmp_path / ".profile")


@pytest.mark.small
def test_registry_write_stores_the_value_and_broadcasts():
    """Check that a registry write stores the value, closes the key and broadcasts."""
    store, values, log = _registry()
    write_user_variable("SUSHISYSTEMS_HOME", "D:/deps", store)
    assert values == {"SUSHISYSTEMS_HOME": "D:/deps"}
    assert log == ["close", "broadcast"]


@pytest.mark.small
def test_registry_read_closes_the_key_without_a_broadcast():
    """Check that a registry read releases the key and announces nothing."""
    store, _values, log = _registry()
    read_user_variable("SUSHISYSTEMS_HOME", store)
    assert log == ["close"]


@pytest.mark.small
def test_registry_remove_deletes_the_value_and_broadcasts():
    """Check that a registry remove deletes the value and broadcasts."""
    store, values, log = _registry()
    values["SUSHISYSTEMS_HOME"] = "D:/deps"
    remove_user_variable("SUSHISYSTEMS_HOME", store)
    assert values == {}
    assert log == ["close", "broadcast"]


@pytest.mark.medium
def test_profile_write_creates_the_block(tmp_path):
    """Check that the first write creates the file with one marked block."""
    profile = tmp_path / ".profile"
    write_user_variable("SUSHISYSTEMS_HOME", "/opt/deps", ProfileEnvironment(profile))
    assert profile.read_text(encoding="utf-8") == (
        f'{BLOCK_BEGIN}\nexport SUSHISYSTEMS_HOME="/opt/deps"\n{BLOCK_END}\n'
    )


@pytest.mark.medium
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


@pytest.mark.medium
def test_profile_write_replaces_the_line_of_a_set_name(tmp_path):
    """Check that a second write replaces the variable's line in place."""
    store = ProfileEnvironment(tmp_path / ".profile")
    store.write("A", "1")
    store.write("B", "2")
    store.write("A", "3")
    text = (tmp_path / ".profile").read_text(encoding="utf-8")
    assert text == f'{BLOCK_BEGIN}\nexport A="3"\nexport B="2"\n{BLOCK_END}\n'


K_HOSTILE = 'C:\\deps "x" $HOME `id`'


@pytest.mark.medium
def test_profile_read_returns_a_hostile_value_unchanged(tmp_path):
    """Check that a value with quotes, dollars and backslashes reads back unchanged."""
    store = ProfileEnvironment(tmp_path / ".profile")
    store.write("A", K_HOSTILE)
    assert read_user_variable("A", store) == K_HOSTILE


@pytest.mark.medium
def test_profile_write_escapes_the_special_characters_in_the_file(tmp_path):
    """Check that the file holds the dollar escaped, so a shell does not expand it."""
    ProfileEnvironment(tmp_path / ".profile").write("A", K_HOSTILE)
    assert '\\$HOME' in (tmp_path / ".profile").read_text(encoding="utf-8")


@pytest.mark.medium
def test_profile_read_returns_none_without_a_file(tmp_path):
    """Check that a read from a missing file returns None and creates nothing."""
    profile = tmp_path / ".profile"
    assert read_user_variable("A", ProfileEnvironment(profile)) is None
    assert not profile.exists()


@pytest.mark.medium
def test_profile_read_ignores_an_export_outside_the_block(tmp_path):
    """Check that a line the user wrote outside the block is not read as stored."""
    profile = tmp_path / ".profile"
    profile.write_text('export A="mine"\n', encoding="utf-8")
    assert ProfileEnvironment(profile).read("A") is None


@pytest.mark.medium
def test_profile_remove_deletes_one_line(tmp_path):
    """Check that a remove deletes the variable's line and keeps the others."""
    store = ProfileEnvironment(tmp_path / ".profile")
    store.write("A", "1")
    store.write("B", "2")
    remove_user_variable("A", store)
    text = (tmp_path / ".profile").read_text(encoding="utf-8")
    assert text == f'{BLOCK_BEGIN}\nexport B="2"\n{BLOCK_END}\n'


@pytest.mark.medium
def test_profile_remove_of_the_last_variable_drops_the_markers(tmp_path):
    """Check that an emptied block leaves the file as it was before the write."""
    profile = tmp_path / ".profile"
    original = 'export PATH="$HOME/bin:$PATH"\n'
    profile.write_text(original, encoding="utf-8")
    store = ProfileEnvironment(profile)
    store.write("A", "1")
    store.remove("A")
    assert profile.read_text(encoding="utf-8") == original


@pytest.mark.medium
def test_profile_remove_of_an_unset_name_writes_nothing(tmp_path):
    """Check that removing a name the block does not hold creates no file."""
    profile = tmp_path / ".profile"
    ProfileEnvironment(profile).remove("A")
    assert not profile.exists()


@pytest.mark.small
@pytest.mark.parametrize(("windows", "kind"), [(True, RegistryEnvironment),
                                               (False, ProfileEnvironment)])
def test_the_default_store_follows_the_platform(windows, kind):
    """Check that the registry is the default on Windows and the profile elsewhere."""
    assert isinstance(default_environment(windows), kind)
