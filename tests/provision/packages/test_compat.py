# test_compat.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the deprecated names ``sushicore.provision.packages`` exported before 0.17.0."""

from __future__ import annotations

import io
import json
import shutil
import sys
import urllib.request

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.provision import packages
from sushicore.provision.default_console import DEFAULT_CONSOLE
from sushicore.provision.packages.github_release import AssetNotFoundError

K_RELEASES = [
    {"tag_name": "v2.0-rc1", "assets": [{"name": "tool-linux.tar.gz", "browser_download_url": "https://x/rc1"}]},
    {"tag_name": "v1.0", "assets": [
        {"name": "tool-win.zip", "browser_download_url": "https://x/win"},
        {"name": "tool-linux.tar.gz", "browser_download_url": "https://x/v1"},
    ]},
]
K_LATEST = {"assets": K_RELEASES[1]["assets"]}


@pytest.fixture
def github(monkeypatch):
    """Answer each GitHub request with the document its URL names, and record the URLs."""
    asked: list[str] = []

    def urlopen(request, timeout=None):
        """Return the latest release, or the list of releases, by what *request* asks for."""
        asked.append(request.full_url)
        document = K_RELEASES if "per_page" in request.full_url else K_LATEST
        return io.BytesIO(json.dumps(document).encode())

    monkeypatch.setattr(urllib.request, "urlopen", urlopen)
    return asked


@pytest.fixture
def console():
    """Bind a recording console as the default one, and unbind it afterwards."""
    recording = RecordingConsole()
    DEFAULT_CONSOLE.bind(lambda: recording)
    yield recording
    DEFAULT_CONSOLE.bind(None)


@pytest.mark.small
def test_the_latest_asset_is_the_first_match_of_the_latest_release(github):
    """Check that the lookup reads the latest release and returns the URL of the first match."""
    with pytest.warns(DeprecationWarning, match="gh_tagged_asset"):
        url = packages.gh_latest_asset("o/r", "*.zip")
    assert (url, github) == ("https://x/win", ["https://api.github.com/repos/o/r/releases/latest"])


@pytest.mark.small
def test_the_latest_asset_without_a_match_raises_the_asset_error(github):
    """Check that a glob nothing matches raises, and the error is still a RuntimeError."""
    with pytest.warns(DeprecationWarning), pytest.raises(AssetNotFoundError) as caught:
        packages.gh_latest_asset("o/r", "*.dmg")
    assert isinstance(caught.value, RuntimeError)


@pytest.mark.small
def test_the_newest_release_asset_is_the_tag_and_url_of_the_first_release_with_a_match(github):
    """Check that a prerelease at the head of the list wins over the stable release."""
    with pytest.warns(DeprecationWarning):
        assert packages.gh_latest_release_asset("o/r", "*linux*") == ("v2.0-rc1", "https://x/rc1")


@pytest.mark.small
def test_the_newest_asset_including_prereleases_is_the_url_alone(github):
    """Check that the one-value form answers the URL of the same asset."""
    with pytest.warns(DeprecationWarning):
        assert packages.gh_latest_asset_including_prerelease("o/r", "*linux*") == "https://x/rc1"


@pytest.mark.small
def test_the_newest_release_asset_falls_through_to_an_older_release(github):
    """Check that a release without a match is skipped."""
    with pytest.warns(DeprecationWarning):
        assert packages.gh_latest_release_asset("o/r", "*.zip") == ("v1.0", "https://x/win")


@pytest.mark.small
def test_the_newest_release_asset_without_a_match_raises_the_asset_error(github):
    """Check that no match in any release raises."""
    with pytest.warns(DeprecationWarning), pytest.raises(AssetNotFoundError):
        packages.gh_latest_release_asset("o/r", "*.dmg")


@pytest.mark.small
def test_a_deprecated_lookup_warns_at_its_caller(github):
    """Check that the warning points at this file."""
    with pytest.warns(DeprecationWarning) as caught:
        packages.gh_latest_asset("o/r", "*.zip")
    assert caught[0].filename == __file__


@pytest.mark.small
def test_the_old_run_echoes_a_dry_run_on_the_default_console_and_starts_nothing(console):
    """Check that a dry run returns 0 and says so on the default console."""
    with pytest.warns(DeprecationWarning, match="process_run.run"):
        code = packages.run(["no-such-program-xyz"], True)
    assert (code, console.texts("info")) == (0, ["(dry-run) not executed"])


@pytest.mark.medium
def test_the_old_run_returns_the_exit_code_of_the_command(console):
    """Check that a command that exits 3 answers 3."""
    with pytest.warns(DeprecationWarning):
        assert packages.run([sys.executable, "-c", "raise SystemExit(3)"], False) == 3


@pytest.mark.medium
def test_the_old_run_with_check_reports_a_failure_once(console):
    """Check that a failed command run with check is one error on the console."""
    with pytest.warns(DeprecationWarning):
        packages.run([sys.executable, "-c", "raise SystemExit(3)"], False, check=True)
    assert console.texts("error") == ["Command failed (3)."]


@pytest.mark.small
def test_priming_sudo_without_sudo_on_the_machine_does_nothing_and_warns(console, monkeypatch):
    """Check that a machine with no sudo is left alone, with the deprecation warning."""
    monkeypatch.setattr(shutil, "which", lambda name: None)
    with pytest.warns(DeprecationWarning, match="sudo prompt") as caught:
        packages.prime_sudo()
    assert (console.texts("warn"), caught[0].filename) == ([], __file__)


@pytest.mark.small
def test_the_package_lists_every_restored_name_in_its_public_names():
    """Check that the star import of the package still brings the five restored names."""
    assert {"gh_latest_asset", "gh_latest_asset_including_prerelease",
            "gh_latest_release_asset", "prime_sudo", "run"} <= set(packages.__all__)
