# test_intel_oneapi_repo.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the Intel oneAPI apt repository setup."""

from __future__ import annotations

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.fragment_types import KeyPin
from sushicore.proc_memory import RecordingRunner
from sushicore.provision.intel_oneapi_repo import (K_ONEAPI_KEY_URL, ensure_intel_oneapi_repo,
                                                   key_fingerprints)

K_FINGERPRINT = "e9bf0afc46d6e8b7da5882f1bac6f0c353d04109"
K_OTHER = "52abd6e87e421793971873ffacfa9fc57e6c5dbe"
K_PIN = KeyPin("oneapi-apt-key", K_FINGERPRINT)


def _pub(fingerprint: str) -> tuple[str, str]:
    """Return the ``pub`` and ``fpr`` records of one primary key."""
    return ("pub:-:2048:1:1A8497B11911E097:1475053901:::-:::sc::::::23::0:",
            f"fpr:::::::::{fingerprint.upper()}:")


def _runner(*listing: str) -> RecordingRunner:
    """Return a runner whose download succeeds and whose key listing prints *listing*."""
    return RecordingRunner(RecordingConsole()).script(0).script(0, listing)


def _configure(runner, console, tmp_path):
    """Run the setup against keyring and source list files that do not exist yet."""
    return ensure_intel_oneapi_repo(False, runner, console=console, key_pin=K_PIN,
                                    keyring=tmp_path / "keyring.gpg",
                                    source_list=tmp_path / "oneAPI.list")


@pytest.mark.small
def test_a_dry_run_of_the_oneapi_repository_succeeds_without_an_error(recording_console, tmp_path):
    """Check that a dry run answers True, records no error and runs no command."""
    runner = RecordingRunner(RecordingConsole())

    assert ensure_intel_oneapi_repo(True, runner, console=recording_console, key_pin=K_PIN,
                                    keyring=tmp_path / "absent.gpg") is True
    assert not [name for name, _ in recording_console.calls if name == "error"]
    assert runner.commands == []


@pytest.mark.small
def test_a_failed_download_is_one_error_and_stops_before_any_key_is_read(recording_console, tmp_path):
    """Check that a download that exits non-zero reports one error and answers False."""
    runner = RecordingRunner(RecordingConsole()).script(1)

    assert _configure(runner, recording_console, tmp_path) is False
    assert [name for name, _ in recording_console.calls].count("error") == 1
    assert len(runner.commands) == 1


@pytest.mark.small
def test_a_key_with_the_pinned_fingerprint_is_installed_through_the_keyring_file(
        recording_console, tmp_path):
    """Check that the key is downloaded to a file, verified, and only then imported and installed."""
    runner = _runner(*_pub(K_OTHER), *_pub(K_FINGERPRINT))

    assert _configure(runner, recording_console, tmp_path) is True

    argv = [list(c.argv) for c in runner.commands]
    assert [step[1] if step[0] == "sudo" else step[0] for step in argv] == [
        "curl", "gpg", "gpg", "gpg", "install", "install"]
    assert argv[0][-1] == K_ONEAPI_KEY_URL
    assert argv[2][-2:] == ["--import", argv[0][3]]
    assert argv[3][-1] == K_FINGERPRINT.upper()
    assert [step[-1] for step in argv[4:]] == [str(tmp_path / "keyring.gpg"),
                                               str(tmp_path / "oneAPI.list")]
    assert recording_console.texts("error") == []


@pytest.mark.small
def test_a_key_with_another_fingerprint_is_refused_and_nothing_is_installed(
        recording_console, tmp_path):
    """Check that a file holding no key with the pinned fingerprint ends with one error and no install."""
    runner = _runner(*_pub(K_OTHER))

    assert _configure(runner, recording_console, tmp_path) is False

    assert [list(c.argv)[0] for c in runner.commands] == ["curl", "gpg"]
    [message] = recording_console.texts("error")
    assert K_FINGERPRINT in message and K_OTHER in message


@pytest.mark.small
def test_a_pinned_fingerprint_on_a_subkey_does_not_count(recording_console, tmp_path):
    """Check that only a primary key can match the pin, so a subkey carrying it is refused."""
    runner = _runner(*_pub(K_OTHER), "sub:-:2048:1:AAAAAAAAAAAAAAAA:1475053901::::::e::::::23:",
                     f"fpr:::::::::{K_FINGERPRINT.upper()}:")

    assert _configure(runner, recording_console, tmp_path) is False
    assert len(runner.commands) == 2


@pytest.mark.small
def test_a_missing_gpg_refuses_the_key(recording_console, tmp_path):
    """Check that no gpg to read the key with is a refusal, never an install."""
    runner = RecordingRunner(RecordingConsole()).script(0).script_missing()

    assert _configure(runner, recording_console, tmp_path) is False
    assert len(runner.commands) == 2


@pytest.mark.small
def test_a_configured_repository_is_left_alone(recording_console, tmp_path):
    """Check that existing keyring and source list files end the setup with no command run."""
    keyring = tmp_path / "keyring.gpg"
    source_list = tmp_path / "oneAPI.list"
    keyring.write_text("")
    source_list.write_text("")
    runner = RecordingRunner(RecordingConsole())
    assert ensure_intel_oneapi_repo(False, runner, console=recording_console,
                                    keyring=keyring, source_list=source_list) is True
    assert runner.commands == []


@pytest.mark.small
def test_the_fingerprints_of_primary_keys_are_read_in_lower_case():
    """Check that each primary key gives one fingerprint and a subkey's is left out."""
    text = "\n".join((*_pub(K_FINGERPRINT), "sub:-:2048:1:BBBB:::::e::::::23:",
                      "fpr:::::::::" + K_OTHER.upper() + ":", *_pub(K_OTHER)))

    assert key_fingerprints(text) == [K_FINGERPRINT, K_OTHER]
