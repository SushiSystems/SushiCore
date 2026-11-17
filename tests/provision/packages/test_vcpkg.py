# test_vcpkg.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the vcpkg package manager's view of what is installed."""

from __future__ import annotations

import pytest

from sushicore.fragment_types import GitPin
from sushicore.proc_memory import RecordingRunner
from sushicore.provision.config import ProvisionSettings
from sushicore.provision.git_client_memory import InMemoryGitClient
from sushicore.provision.packages.vcpkg import VcpkgManager


#: One line of `vcpkg list --triplet x64-windows` output for an installed imgui.
LISTED = "imgui:x64-windows                        1.92.8    Dear ImGui\n"


@pytest.fixture
def manager(tmp_path, recording_console):
    """Return a Windows VcpkgManager with a vcpkg file under a folder of its own, listing imgui alone."""
    (tmp_path / "vcpkg.exe").write_text("")
    runner = RecordingRunner(recording_console).script(0, (LISTED.rstrip(),))
    return VcpkgManager(ProvisionSettings(platform="windows", vcpkg_root=str(tmp_path)), runner,
                        console=recording_console)


@pytest.mark.medium
@pytest.mark.parametrize(("package", "installed"), [
    ("imgui[glfw-binding,opengl3-binding]", True),
    ("imgui", True),
    ("glfw3[wayland]", False),
], ids=["a port with features", "a bare port name", "a port that is not listed"])
def test_a_port_is_installed_when_the_listing_holds_its_name(manager, package, installed):
    """Check that a port reads as installed by its name, with or without features."""
    assert manager.is_installed(package) is installed


#: The commit the tests pin and a different one a checkout can land on.
K_COMMIT = "528cfa41f4b1578b16ac6b2f6d2e6f98e5308d2d"
K_OTHER = "0123456789abcdef0123456789abcdef01234567"
K_PIN = GitPin("vcpkg", "master", K_COMMIT)


def _fetching(tmp_path, console, git, runner=None):
    """Return a Windows manager over a root with no executable, fetching through *git*."""
    return VcpkgManager(ProvisionSettings(platform="windows", vcpkg_root=str(tmp_path / "vcpkg")),
                        runner or RecordingRunner(console), console=console, git=git, pin=K_PIN)


@pytest.mark.medium
def test_vcpkg_is_fetched_by_its_pinned_commit_and_then_bootstrapped(tmp_path, recording_console):
    """Check that a fresh root is fetched in full at the pinned hash and bootstrapped once HEAD matches."""
    git = InMemoryGitClient()
    runner = RecordingRunner(recording_console)

    assert _fetching(tmp_path, recording_console, git, runner).ensure_bootstrapped(False) is True

    assert git.checkouts == [("https://github.com/microsoft/vcpkg.git", K_COMMIT,
                              tmp_path / "vcpkg", False, False)]
    assert [c.argv[0] for c in runner.commands] == ["cmd"]


@pytest.mark.medium
def test_a_vcpkg_checkout_off_the_pin_is_one_error_and_is_not_bootstrapped(
        tmp_path, recording_console):
    """Check that a fetch ending at another commit stops before the bootstrap script runs."""
    git = InMemoryGitClient(checkout_head=K_OTHER)
    runner = RecordingRunner(recording_console)

    assert _fetching(tmp_path, recording_console, git, runner).ensure_bootstrapped(False) is False

    assert runner.commands == []
    [message] = recording_console.texts("error")
    assert K_COMMIT in message and K_OTHER in message


@pytest.mark.medium
def test_an_existing_vcpkg_tree_at_another_commit_is_refused(tmp_path, recording_console):
    """Check that a tree already cloned is confirmed against the pin, not trusted."""
    (tmp_path / "vcpkg" / ".git").mkdir(parents=True)
    git = InMemoryGitClient(default_head=K_OTHER)
    runner = RecordingRunner(recording_console)

    assert _fetching(tmp_path, recording_console, git, runner).ensure_bootstrapped(False) is False

    assert (git.checkouts, runner.commands) == ([], [])
    assert recording_console.texts("error")


@pytest.mark.medium
def test_an_existing_vcpkg_tree_at_the_pin_is_bootstrapped_without_a_fetch(
        tmp_path, recording_console):
    """Check that a tree already at the pinned commit is bootstrapped and fetched again by no one."""
    (tmp_path / "vcpkg" / ".git").mkdir(parents=True)
    git = InMemoryGitClient(default_head=K_COMMIT)
    runner = RecordingRunner(recording_console)

    assert _fetching(tmp_path, recording_console, git, runner).ensure_bootstrapped(False) is True

    assert git.checkouts == []
    assert [c.argv[0] for c in runner.commands] == ["cmd"]


@pytest.mark.medium
def test_a_failed_vcpkg_fetch_stops_the_bootstrap(tmp_path, recording_console):
    """Check that a fetch git cannot make answers False and bootstraps nothing."""
    runner = RecordingRunner(recording_console)

    assert _fetching(tmp_path, recording_console, InMemoryGitClient(clones=False),
                     runner).ensure_bootstrapped(False) is False
    assert runner.commands == []
