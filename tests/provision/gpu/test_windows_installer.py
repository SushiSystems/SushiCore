# test_windows_installer.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Pure, fake-backed pieces of the Windows installer plumbing."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

import pytest

from sushicore.provision.gpu.windows_installer import (
    ELEVATION_DECLINED,
    LAUNCH_FAILED,
    ElevatedResult,
    HttpDownloader,
    InstallerDownload,
    MachineEnvironment,
    PowerShellElevatedRunner,
    RegistryMachineEnvironment,
    adopt_machine_variable,
    merged_path,
    prepend_machine_path,
)
from sushicore.provision.gpu.windows_installer_memory import InMemoryMachineEnvironment

_BODY = b"installer bytes"
_MD5 = hashlib.md5(_BODY).hexdigest()
_DOWNLOAD = InstallerDownload("https://example.invalid/setup.exe", "setup.exe", _MD5)


class _OfflineUrl:
    """Opens no URL: every call raises :class:`OSError` and is counted."""

    def __init__(self) -> None:
        """Start with no calls."""
        self.calls = 0

    def __call__(self, *args, **kwargs):
        """Count the call and raise as an unreachable host does."""
        self.calls += 1
        raise OSError("offline")


@pytest.mark.small
def test_command_quotes_an_apostrophe_in_the_executable_path():
    """Check that a single quote in the path is doubled inside the PowerShell literal."""
    path = Path("C:/App's Name/setup.exe")
    argv = PowerShellElevatedRunner().command(path, [])

    assert "-FilePath '" + str(path).replace("'", "''") + "'" in argv[-1]


@pytest.mark.small
def test_command_starts_powershell_without_profile_or_prompt():
    """Check that the argv head runs the script non-interactively."""
    argv = PowerShellElevatedRunner().command(Path("setup.exe"), [])

    assert argv[:-1] == ["powershell", "-NoProfile", "-NonInteractive", "-Command"]


@pytest.mark.small
def test_command_runs_the_executable_with_its_arguments_elevated():
    """Check that the script names the executable and the joined arguments under RunAs."""
    path = Path("C:/installers/setup.exe")
    argv = PowerShellElevatedRunner().command(path, ["/quiet", "/norestart"])

    script = argv[-1]
    assert f"Start-Process -FilePath '{path}'" in script
    assert "-ArgumentList '/quiet /norestart' -Verb RunAs" in script


@pytest.mark.small
def test_command_exits_with_the_declined_and_launch_failed_codes():
    """Check that a declined prompt and a failed launch each have their own exit code."""
    script = PowerShellElevatedRunner().command(Path("setup.exe"), [])[-1]

    assert f"NativeErrorCode -eq {ELEVATION_DECLINED}) {{ exit {ELEVATION_DECLINED} }}" in script
    assert f"exit {LAUNCH_FAILED} }}" in script


@pytest.mark.small
def test_run_reports_a_process_that_cannot_start_as_launch_failed():
    """Check that an OSError from the process start becomes LAUNCH_FAILED with its text."""
    def run(*args, **kwargs):
        """Fail as a missing PowerShell does."""
        raise OSError("powershell is missing")

    result = PowerShellElevatedRunner(run=run).run(Path("setup.exe"), [])

    assert result == ElevatedResult(LAUNCH_FAILED, "powershell is missing")


@pytest.mark.small
@pytest.mark.parametrize(("process", "machine", "expected"), [
    ("existing", "new;existing", "new;existing"),
    ("existing", "Existing;new", "new;existing"),
    ("existing", "existing", "existing"),
    ("", "new", "new"),
], ids=["adds-only-the-fresh-entries", "dedupes-case-insensitively", "nothing-fresh",
        "empty-process-path"])
def test_merged_path_puts_the_fresh_machine_entries_first(process, machine, expected):
    """Check that machine entries missing from the process PATH come first, compared by lower case."""
    assert merged_path(process.replace(";", os.pathsep), machine.replace(";", os.pathsep)) ==         expected.replace(";", os.pathsep)


@pytest.mark.medium
def test_prepend_machine_path_sets_the_process_path(monkeypatch):
    """Check that the merged PATH is written to this process's environment."""
    monkeypatch.setenv("PATH", "existing")

    prepend_machine_path(InMemoryMachineEnvironment({"Path": "new"}))

    assert os.environ["PATH"] == os.pathsep.join(["new", "existing"])


@pytest.mark.medium
def test_adopt_machine_variable_copies_the_machine_value_into_the_process(monkeypatch):
    """Check that a set machine variable is returned and written to os.environ."""
    monkeypatch.delenv("SUSHI_TEST_MACHINE_VARIABLE", raising=False)
    environment = InMemoryMachineEnvironment({"SUSHI_TEST_MACHINE_VARIABLE": "machine value"})

    adopted = adopt_machine_variable(environment, "SUSHI_TEST_MACHINE_VARIABLE")

    assert adopted == "machine value"
    assert os.environ["SUSHI_TEST_MACHINE_VARIABLE"] == "machine value"


@pytest.mark.medium
def test_adopt_machine_variable_of_an_unset_variable_is_none(monkeypatch):
    """Check that an unset machine variable returns None and leaves os.environ alone."""
    monkeypatch.delenv("SUSHI_TEST_MACHINE_VARIABLE", raising=False)

    adopted = adopt_machine_variable(InMemoryMachineEnvironment(), "SUSHI_TEST_MACHINE_VARIABLE")

    assert adopted is None
    assert "SUSHI_TEST_MACHINE_VARIABLE" not in os.environ


@pytest.mark.small
def test_registry_environment_reads_an_absent_value_as_none():
    """Check that a value the registry does not hold reads as None."""
    def query(name):
        """Fail as the registry does for an absent value."""
        raise FileNotFoundError(name)

    assert RegistryMachineEnvironment(query=query).read("Absent") is None


@pytest.mark.medium
def test_fetch_reuses_a_copy_whose_md5_matches(tmp_path, recording_console):
    """Check that a stored installer with the published MD5 is returned without a download."""
    (tmp_path / "setup.exe").write_bytes(_BODY)
    open_url = _OfflineUrl()

    fetched = HttpDownloader(open_url=open_url).fetch(_DOWNLOAD, tmp_path)

    assert fetched == tmp_path / "setup.exe"
    assert open_url.calls == 0


@pytest.mark.medium
def test_fetch_deletes_a_copy_whose_md5_does_not_match(tmp_path, recording_console):
    """Check that a stored installer with another MD5 is removed before the download starts."""
    (tmp_path / "setup.exe").write_bytes(b"truncated")

    HttpDownloader(open_url=_OfflineUrl()).fetch(_DOWNLOAD, tmp_path)

    assert not (tmp_path / "setup.exe").exists()


@pytest.mark.medium
def test_fetch_returns_none_and_warns_when_the_download_fails(tmp_path, recording_console):
    """Check that an unreachable host gives None and one warning naming the file and the error."""
    fetched = HttpDownloader(open_url=_OfflineUrl()).fetch(_DOWNLOAD, tmp_path)

    assert fetched is None
    assert recording_console.texts("warn") == ["Download of setup.exe failed: offline"]


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
