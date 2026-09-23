# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Pure, fake-backed pieces of the Windows installer plumbing."""

from __future__ import annotations

import os

from sushicore.provision.gpu.windows_installer import (
    ELEVATION_DECLINED,
    LAUNCH_FAILED,
    PowerShellElevatedRunner,
    _ps_quote,
    prepend_machine_path,
)


def test_ps_quote_escapes_a_single_quote_and_keeps_spaces_and_backslashes():
    assert _ps_quote(r"C:\Program Files\App's Name") == r"'C:\Program Files\App''s Name'"


def test_powershell_elevated_runner_command_builds_the_expected_argv():
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


class _FakeEnvironment:
    """A :class:`MachineEnvironment` stand-in returning a fixed value per name."""

    def __init__(self, values: dict[str, str]) -> None:
        """Store *values* to answer :meth:`read` from, never touching the registry."""
        self._values = values

    def read(self, name: str) -> str | None:
        """Return the fixed value recorded for *name*, or None when absent."""
        return self._values.get(name)


def test_prepend_machine_path_adds_only_the_entries_not_already_on_path(monkeypatch):
    monkeypatch.setenv("PATH", r"C:\Existing")
    fake = _FakeEnvironment({"Path": r"C:\New" + os.pathsep + r"C:\Existing"})

    prepend_machine_path(fake)

    assert os.environ["PATH"] == r"C:\New" + os.pathsep + r"C:\Existing"


def test_prepend_machine_path_dedupes_case_insensitively(monkeypatch):
    monkeypatch.setenv("PATH", r"C:\existing")
    fake = _FakeEnvironment({"Path": r"C:\Existing" + os.pathsep + r"C:\New"})

    prepend_machine_path(fake)

    assert os.environ["PATH"] == r"C:\New" + os.pathsep + r"C:\existing"


def test_prepend_machine_path_leaves_path_untouched_when_nothing_is_fresh(monkeypatch):
    monkeypatch.setenv("PATH", r"C:\Existing")
    fake = _FakeEnvironment({"Path": r"C:\Existing"})

    prepend_machine_path(fake)

    assert os.environ["PATH"] == r"C:\Existing"


def test_prepend_machine_path_handles_an_empty_process_path(monkeypatch):
    monkeypatch.setenv("PATH", "")
    fake = _FakeEnvironment({"Path": r"C:\New"})

    prepend_machine_path(fake)

    assert os.environ["PATH"] == r"C:\New"
