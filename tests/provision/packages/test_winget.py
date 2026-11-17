# test_winget.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the winget package manager."""

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.proc_memory import RecordingRunner
from sushicore.provision.licence_consent import Licence, LicenceConsent
from sushicore.provision.licence_consent_memory import granted_consent
from sushicore.provision.packages import winget

K_LINK = "https://licences.example/own"
K_LISTING = ("Name Id", "Git Git.Git 2.4")


@pytest.fixture
def runner(recording_console) -> RecordingRunner:
    """Build the runner that records the commands of the winget manager and starts none."""
    return RecordingRunner(recording_console)


@pytest.fixture
def consented(runner, recording_console):
    """Builds the winget manager of a run whose user consented to the licence of package A and B."""
    return winget.WingetManager(granted_consent(Licence("A", K_LINK), Licence("B", K_LINK)),
                                show=lambda command: f"License Url: {K_LINK}\n", runner=runner,
                                console=recording_console)


def _argv(runner: RecordingRunner) -> list[list[str]]:
    """Return the commands *runner* was asked to run, as lists."""
    return [list(command.argv) for command in runner.commands]


@pytest.mark.small
def test_available_follows_the_path(monkeypatch, recording_console):
    """Check that winget is unavailable when it is not on PATH."""
    monkeypatch.setattr(winget.shutil, "which", lambda name: None)
    assert not winget.WingetManager(console=recording_console).available()


@pytest.mark.small
def test_available_is_true_when_winget_is_on_the_path(monkeypatch, recording_console):
    """Check that winget is available when it is on PATH."""
    monkeypatch.setattr(winget.shutil, "which", lambda name: "C:/winget.exe")
    assert winget.WingetManager(console=recording_console).available()


@pytest.mark.small
@pytest.mark.parametrize(("package", "installed"), [
    ("git.git", True), ("Kitware.CMake", False), ("Git.G", False),
], ids=["the id in any case", "an id not listed", "part of an id is not the id"])
def test_is_installed_needs_the_whole_id_in_the_listing(runner, package, installed,
                                                        recording_console):
    """Check that a package reads as installed only when its whole id is in the listing."""
    runner.script(0, K_LISTING)
    assert winget.WingetManager(runner=runner,
                                console=recording_console).is_installed(package) is installed


@pytest.mark.small
def test_is_installed_is_false_when_winget_cannot_run(runner, recording_console):
    """Check that a winget that cannot start reads as nothing installed."""
    runner.script_missing()
    assert not winget.WingetManager(runner=runner,
                                    console=recording_console).is_installed("Git.Git")


@pytest.mark.small
def test_install_runs_one_silent_command_per_package(runner, consented):
    """Check that each package gets its own silent winget command."""
    consented.install(["A", "B"], dry_run=False)
    commands = _argv(runner)
    assert [command[3] for command in commands] == ["A", "B"]
    assert all("--silent" in command for command in commands)


@pytest.mark.small
def test_install_reports_a_failed_package(runner, consented):
    """Check that one failing package makes the install answer False."""
    runner.script(0).script(1)
    assert not consented.install(["A", "B"], dry_run=False)


@pytest.mark.small
def test_remove_uninstalls_each_package(runner, recording_console):
    """Check that remove starts one silent uninstall per package."""
    assert winget.WingetManager(runner=runner, console=recording_console).remove(["A"],
                                                                                 dry_run=False)
    assert _argv(runner) == [["winget", "uninstall", "--id", "A", "-e", "--silent"]]


@pytest.mark.small
def test_install_passes_the_agreement_flags_after_consent(runner, consented):
    """Check that a consented install hands winget both agreement flags."""
    consented.install(["A"], dry_run=False)
    assert {"--accept-package-agreements", "--accept-source-agreements"} <= set(_argv(runner)[0])


@pytest.mark.small
def test_install_without_consent_runs_nothing(runner, recording_console):
    """Check that an install no consent covers starts no winget command and fails."""
    manager = winget.WingetManager(show=lambda command: "", runner=runner,
                                   console=recording_console)
    assert not manager.install(["A"], dry_run=False)
    assert _argv(runner) == []


@pytest.mark.small
def test_the_licence_of_a_package_is_its_own_page_read_through_winget_show(runner,
                                                                           recording_console):
    """Check that the licence names the package and links the page winget show prints for it."""
    runner.script(0, ("Version: 1", "  License Url: https://git.example/licence"))
    manager = winget.WingetManager(runner=runner, console=recording_console)

    held = manager.licence_of("Git.Git")

    assert (held, _argv(runner)) == (Licence("Git.Git", "https://git.example/licence"),
                                     [["winget", "show", "--id", "Git.Git", "-e"]])


@pytest.mark.small
def test_the_consent_lists_the_package_licence_with_its_own_url(recording_console):
    """Check that the question names the package's own licence link, read before asking."""
    console = RecordingConsole(answer="y")
    manager = winget.WingetManager(show=lambda command: "License Url: https://pkg.example/eula\n",
                                   console=recording_console)

    LicenceConsent(console, accept_flag=False).request([manager.licence_of("Pkg.Id")])

    assert console.texts("info") == ["  Pkg.Id: https://pkg.example/eula"]


@pytest.mark.small
def test_install_refuses_a_package_whose_licence_the_consent_does_not_cover(runner,
                                                                            recording_console):
    """Check that consent to one package's licence does not let another package install."""
    manager = winget.WingetManager(granted_consent(Licence("A", K_LINK)),
                                   show=lambda command: "License Url: https://other.example\n",
                                   runner=runner, console=recording_console)

    assert not manager.install(["A"], dry_run=False)
    assert _argv(runner) == []
