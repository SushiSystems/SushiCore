# test_windows_installer.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Pure, fake-backed pieces of the Windows installer plumbing."""

from __future__ import annotations

import os
from dataclasses import dataclass

import pytest

from sushicore.provision.gpu.windows_installer import (
    ELEVATION_DECLINED,
    LAUNCH_FAILED,
    MachineEnvironment,
    PowerShellElevatedRunner,
    RegistryMachineEnvironment,
    _ps_quote,
    prepend_machine_path,
)
from sushicore.provision.gpu.windows_installer_memory import InMemoryMachineEnvironment




@pytest.mark.small
def test_ps_quote_escapes_a_single_quote_and_keeps_spaces_and_backslashes():
    """Check that ps quote escapes a single quote and keeps spaces and backslashes."""
    assert _ps_quote(r"C:\Program Files\App's Name") == r"'C:\Program Files\App''s Name'"


@pytest.mark.small
def test_powershell_elevated_runner_command_builds_the_expected_argv():
    """Check that powershell elevated runner command builds the expected argv."""
    exe = "C:/installers/setup.exe"
    args = ["/quiet", "/norestart"]

    argv = PowerShellElevatedRunner().command(exe, args)

    script = (
        "try { $p = Start-Process -FilePath 'C:/installers/setup.exe' "
        "-ArgumentList '/quiet /norestart' -Verb RunAs -Wait -PassThru "
        "-ErrorAction Stop; exit $p.ExitCode } "
        "catch { $e = $_.Exception; while ($e) { "
        f"if ($e.NativeErrorCode -eq {ELEVATION_DECLINED}) {{ exit {ELEVATION_DECLINED} }}; "
        "$e = $e.InnerException }; "
        f"[Console]::Error.WriteLine($_.Exception.Message); exit {LAUNCH_FAILED} }}"
    )
    assert argv == ["powershell", "-NoProfile", "-NonInteractive", "-Command", script]


@pytest.mark.skipif(os.name != "nt", reason="a drive-letter path holds the POSIX path separator")
@pytest.mark.small
def test_prepend_machine_path_adds_only_the_entries_not_already_on_path(monkeypatch):
    """Check that prepend machine path adds only the entries not already on path."""
    monkeypatch.setenv("PATH", r"C:\Existing")
    fake = InMemoryMachineEnvironment({"Path": r"C:\New" + os.pathsep + r"C:\Existing"})

    prepend_machine_path(fake)

    assert os.environ["PATH"] == r"C:\New" + os.pathsep + r"C:\Existing"


@pytest.mark.skipif(os.name != "nt", reason="a drive-letter path holds the POSIX path separator")
@pytest.mark.small
def test_prepend_machine_path_dedupes_case_insensitively(monkeypatch):
    """Check that prepend machine path dedupes case insensitively."""
    monkeypatch.setenv("PATH", r"C:\existing")
    fake = InMemoryMachineEnvironment({"Path": r"C:\Existing" + os.pathsep + r"C:\New"})

    prepend_machine_path(fake)

    assert os.environ["PATH"] == r"C:\New" + os.pathsep + r"C:\existing"


@pytest.mark.small
def test_prepend_machine_path_leaves_path_untouched_when_nothing_is_fresh(monkeypatch):
    """Check that prepend machine path leaves path untouched when nothing is fresh."""
    monkeypatch.setenv("PATH", r"C:\Existing")
    fake = InMemoryMachineEnvironment({"Path": r"C:\Existing"})

    prepend_machine_path(fake)

    assert os.environ["PATH"] == r"C:\Existing"


@pytest.mark.small
def test_prepend_machine_path_handles_an_empty_process_path(monkeypatch):
    """Check that prepend machine path handles an empty process path."""
    monkeypatch.setenv("PATH", "")
    fake = InMemoryMachineEnvironment({"Path": r"C:\New"})

    prepend_machine_path(fake)

    assert os.environ["PATH"] == r"C:\New"



@dataclass
class EnvironmentWorld:
    """A machine environment under test and one variable it is known to hold."""

    environment: MachineEnvironment
    name: str
    value: str


class MachineEnvironmentContract:
    """The promises every :class:`MachineEnvironment` keeps; a subclass supplies the world."""

    def test_a_set_variable_reads_as_its_machine_value(self, world):
        assert world.environment.read(world.name) == world.value

    def test_a_variable_that_is_not_set_reads_as_none(self, world):
        assert world.environment.read("SUSHI_NO_SUCH_MACHINE_VARIABLE") is None


@pytest.mark.small
class TestInMemoryMachineEnvironmentKeepsTheMachineEnvironmentContract(
        MachineEnvironmentContract):
    """The dictionary-backed environment."""

    @pytest.fixture
    def world(self):
        return EnvironmentWorld(InMemoryMachineEnvironment({"OS": "Windows_NT"}), "OS", "Windows_NT")


@pytest.mark.medium
@pytest.mark.skipif(os.name != "nt", reason="the registry exists on Windows only")
class TestRegistryMachineEnvironmentKeepsTheMachineEnvironmentContract(
        MachineEnvironmentContract):
    """The registry reader, on the OS variable every Windows machine stores."""

    @pytest.fixture
    def world(self):
        return EnvironmentWorld(RegistryMachineEnvironment(), "OS", "Windows_NT")
