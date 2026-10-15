# test_oneapi.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Fake-backed tests for the oneAPI installer."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore import provision

from sushicore.provision.config import ProvisionSettings

from sushicore.provision.pipeline import InstallContext, ToolchainSelection

from sushicore.provision.toolchains import oneapi



pytestmark = pytest.mark.medium



class _StatusContext:
    """A no-op stand-in for the Rich ``console.status`` context manager."""

    def __enter__(self):
        """Return this context unchanged."""
        return self

    def __exit__(self, *exc_info):
        """Swallow nothing; let any exception propagate."""
        return False



class _InnerConsole:
    """Stands in for ``Console.console``, the raw Rich console."""

    def print(self, *args, **kwargs):
        """Discard the call."""

    def status(self, *args, **kwargs):
        """Return a no-op status context."""
        return _StatusContext()



class FakeConsole:
    """Records every semantic call; answers ``is_machine``/``prompt`` on demand."""

    def __init__(self, machine: bool = False, answer: str = "n") -> None:
        """Start with no recorded calls, in interactive mode by default."""
        self.calls: list[tuple[str, tuple]] = []
        self.console = _InnerConsole()
        self._machine = machine
        self._answer = answer

    def __getattr__(self, name: str):
        """Return a recorder for any semantic console method name."""
        def record(*args, **_kwargs):
            """Check that record."""
            self.calls.append((name, args))
        return record

    def is_machine(self) -> bool:
        """Report the fixed machine-mode flag this fake was built with."""
        return self._machine

    def prompt(self, _message: str, _default: str) -> str:
        """Return the fixed answer this fake was built with."""
        return self._answer

    def has_call(self, name: str) -> bool:
        """Report whether *name* was recorded at least once."""
        return any(call[0] == name for call in self.calls)



@pytest.fixture
def fake_console():
    """Bind a :class:`FakeConsole` for the test, then unbind it."""
    fake = FakeConsole()
    provision.bind_console(lambda: fake)
    yield fake
    provision.bind_console(None)



def _ctx(oneapi_selected: bool, dry_run: bool = False, detected: dict | None = None
         ) -> InstallContext:
    """Check that ctx."""
    return InstallContext(
        cfg=ProvisionSettings(),
        selection=ToolchainSelection(oneapi=oneapi_selected),
        dry_run=dry_run,
        detected=detected or {},
    )



def test_install_oneapi_noop_when_not_selected(fake_console):
    """Check that install oneapi noop when not selected."""
    assert oneapi.install_oneapi(_ctx(oneapi_selected=False)) is True
    assert fake_console.calls == []



def test_install_oneapi_noop_when_a_sycl_compiler_is_already_detected(fake_console):
    """Check that install oneapi noop when a sycl compiler is already detected."""
    ctx = _ctx(oneapi_selected=True, detected={"sycl_compiler": True})

    assert oneapi.install_oneapi(ctx) is True
    assert fake_console.calls == []



def test_install_oneapi_dry_run_skips_the_download(fake_console):
    """Check that install oneapi dry run skips the download."""
    ctx = _ctx(oneapi_selected=True, dry_run=True)

    assert oneapi.install_oneapi(ctx) is True
    assert fake_console.has_call("info")



def test_install_oneapi_fails_when_the_download_fails(monkeypatch, fake_console):
    """Check that install oneapi fails when the download fails."""
    monkeypatch.setattr(oneapi, "download_oneapi_installer", lambda: None)

    assert oneapi.install_oneapi(_ctx(oneapi_selected=True)) is False



def test_install_oneapi_runs_the_installer_after_a_successful_download(monkeypatch, fake_console):
    """Check that install oneapi runs the installer after a successful download."""
    seen = {}
    monkeypatch.setattr(oneapi, "download_oneapi_installer", lambda: Path("fake.exe"))

    def fake_run(installer):
        """Check that fake run."""
        seen["installer"] = installer
        return True

    monkeypatch.setattr(oneapi, "run_oneapi_installer", fake_run)

    assert oneapi.install_oneapi(_ctx(oneapi_selected=True)) is True
    assert seen["installer"] == Path("fake.exe")



def test_download_oneapi_installer_reuses_an_existing_file(tmp_path, monkeypatch, fake_console):
    """Check that download oneapi installer reuses an existing file."""
    monkeypatch.setattr(oneapi.Path, "home", classmethod(lambda cls: tmp_path))
    existing = tmp_path / "intel-oneapi-toolkit-offline.exe"
    existing.touch()
    monkeypatch.setattr(oneapi.subprocess, "run",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("no curl")))

    assert oneapi.download_oneapi_installer() == existing



class _FakeCompletedProcess:
    """Fake FakeCompletedProcess for testing."""
    def __init__(self, returncode: int) -> None:
        """Perform  init  ."""
        self.returncode = returncode



def test_download_oneapi_installer_downloads_with_curl(tmp_path, monkeypatch, fake_console):
    """Check that download oneapi installer downloads with curl."""
    monkeypatch.setattr(oneapi.Path, "home", classmethod(lambda cls: tmp_path))
    calls = []

    def fake_run(cmd):
        """Check that fake run."""
        calls.append(cmd)
        return _FakeCompletedProcess(0)

    monkeypatch.setattr(oneapi.subprocess, "run", fake_run)

    result = oneapi.download_oneapi_installer()

    assert result == tmp_path / "intel-oneapi-toolkit-offline.exe"
    assert calls[0][0] == "curl"



def test_download_oneapi_installer_returns_none_on_curl_failure(tmp_path, monkeypatch,
                                                                 fake_console):
    """Check that download oneapi installer returns none on curl failure."""
    monkeypatch.setattr(oneapi.Path, "home", classmethod(lambda cls: tmp_path))
    monkeypatch.setattr(oneapi.subprocess, "run", lambda cmd: _FakeCompletedProcess(1))

    result = oneapi.download_oneapi_installer()

    assert result is None
    assert fake_console.has_call("error")



def test_run_oneapi_installer_reports_success(monkeypatch, fake_console):
    """Check that run oneapi installer reports success."""
    monkeypatch.setattr(oneapi.subprocess, "run", lambda cmd: _FakeCompletedProcess(0))

    assert oneapi.run_oneapi_installer(Path("installer.exe")) is True
    assert fake_console.has_call("success")



def test_run_oneapi_installer_reports_failure(monkeypatch, fake_console):
    """Check that run oneapi installer reports failure."""
    monkeypatch.setattr(oneapi.subprocess, "run", lambda cmd: _FakeCompletedProcess(1))

    assert oneapi.run_oneapi_installer(Path("installer.exe")) is False
    assert fake_console.has_call("warn")



def test_run_oneapi_installer_elevates_on_uac_required(monkeypatch, fake_console):
    """Check that run oneapi installer elevates on uac required."""
    calls = []

    def fake_run(cmd, **kwargs):
        """Check that fake run."""
        calls.append(cmd)
        if len(calls) == 1:
            err = OSError("needs elevation")
            err.winerror = oneapi._ELEVATION_REQUIRED
            raise err
        return _FakeCompletedProcess(0)

    monkeypatch.setattr(oneapi.subprocess, "run", fake_run)

    result = oneapi.run_oneapi_installer(Path("installer.exe"))

    assert result is True
    assert len(calls) == 2
    assert calls[1][0] == "powershell"



def test_run_oneapi_installer_reports_a_non_elevation_launch_failure(monkeypatch, fake_console):
    """Check that run oneapi installer reports a non elevation launch failure."""
    def fake_run(cmd, **kwargs):
        """Check that fake run."""
        raise OSError("no such file")

    monkeypatch.setattr(oneapi.subprocess, "run", fake_run)

    result = oneapi.run_oneapi_installer(Path("installer.exe"))

    assert result is False
    assert fake_console.has_call("warn")



def test_run_oneapi_installer_reports_an_elevated_launch_exception(monkeypatch, fake_console):
    """Check that run oneapi installer reports an elevated launch exception."""
    calls = []

    def fake_run(cmd, **kwargs):
        """Check that fake run."""
        calls.append(cmd)
        if len(calls) == 1:
            err = OSError("needs elevation")
            err.winerror = oneapi._ELEVATION_REQUIRED
            raise err
        raise RuntimeError("powershell missing")

    monkeypatch.setattr(oneapi.subprocess, "run", fake_run)

    result = oneapi.run_oneapi_installer(Path("installer.exe"))

    assert result is False
    assert fake_console.has_call("error")
