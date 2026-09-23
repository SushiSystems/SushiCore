# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The Windows CUDA locator downloads, elevates and refreshes the environment through fakes."""

from __future__ import annotations

import hashlib
import http.client
import os
import pathlib
import subprocess
from types import SimpleNamespace

import pytest

from sushicore.provision import probe
from sushicore.provision.gpu import windows_installer as wi
from sushicore.provision.gpu.cuda import WindowsCudaLocator

_ARGS = ("-s", "nvcc_12.6", "cudart_12.6", "nvml_dev_12.6", "-n")
_CFG = SimpleNamespace(platform="windows")


def _warnings(recording_console) -> list[str]:
    """Return the messages recorded on the console's ``warn`` calls."""
    return [args[0] for name, args in recording_console.calls if name == "warn"]


def _successes(recording_console) -> list[str]:
    """Return the messages recorded on the console's ``success`` calls."""
    return [args[0] for name, args in recording_console.calls if name == "success"]


def _commands(recording_console) -> list[str]:
    """Return the commands recorded on the console's ``command`` calls."""
    return [args[0] for name, args in recording_console.calls if name == "command"]


@pytest.fixture(autouse=True)
def _clean_environment(monkeypatch):
    """Start every test with no process CUDA_PATH and a PATH the test can inspect."""
    monkeypatch.delenv("CUDA_PATH", raising=False)
    monkeypatch.setenv("PATH", r"C:\Windows")


class _FakeDownloader:
    """Records fetches and returns a fixed file, or None to simulate a failed download."""

    def __init__(self, result: pathlib.Path | None) -> None:
        """Store the path every fetch returns."""
        self._result = result
        self.fetched: list[tuple[wi.InstallerDownload, pathlib.Path]] = []

    def fetch(self, download, dest_dir):
        """Record the request and return the stored path."""
        self.fetched.append((download, dest_dir))
        return self._result


class _FakeRunner:
    """Records elevated runs and returns a fixed result."""

    def __init__(self, code: int, message: str = "", on_run=None) -> None:
        """Store the result and an optional side effect applied on run."""
        self._result = wi.ElevatedResult(code, message)
        self._on_run = on_run
        self.runs: list[tuple[pathlib.Path, tuple[str, ...]]] = []

    def command(self, exe, args):
        """Return a recognisable command line."""
        return ["elevate", str(exe), *args]

    def run(self, exe, args):
        """Record the run, apply the side effect and return the result."""
        self.runs.append((exe, tuple(args)))
        if self._on_run:
            self._on_run()
        return self._result


class _FakeEnvironment:
    """Returns machine environment values from a dict the test may change."""

    def __init__(self, values: dict[str, str] | None = None) -> None:
        """Store the machine values."""
        self.values = dict(values or {})

    def read(self, name):
        """Return the stored value for *name*, or None."""
        return self.values.get(name)


def _tools(tmp_path, downloader, runner, environment=None) -> wi.WindowsInstallerTools:
    """Bundle fakes with a destination folder under *tmp_path*."""
    return wi.WindowsInstallerTools(downloader=downloader, runner=runner,
                                    environment=environment or _FakeEnvironment(),
                                    dest_dir=lambda: tmp_path / "installers")


def _toolkit(root: pathlib.Path) -> pathlib.Path:
    """Create a fake toolkit with bin/nvcc.exe under *root*."""
    (root / "bin").mkdir(parents=True, exist_ok=True)
    (root / "bin" / "nvcc.exe").write_text("")
    return root


def _installer(tmp_path) -> pathlib.Path:
    """Create the installer file a fake download reports."""
    exe = tmp_path / "installers" / "cuda_12.6.3_windows_network.exe"
    exe.parent.mkdir(parents=True, exist_ok=True)
    exe.write_bytes(b"exe")
    return exe


def test_absent_toolkit_downloads_and_runs_the_silent_install(tmp_path, recording_console):
    """Check that absent toolkit downloads and runs the silent install."""
    exe = _installer(tmp_path)
    downloader, runner = _FakeDownloader(exe), _FakeRunner(0)

    assert WindowsCudaLocator(_tools(tmp_path, downloader, runner)).provision(_CFG, False)

    download, dest = downloader.fetched[0]
    assert download.url == ("https://developer.download.nvidia.com/compute/cuda/12.6.3/"
                            "network_installers/cuda_12.6.3_windows_network.exe")
    assert download.md5 == "48d5d66c3550b7744715c638dac4f522"
    assert dest == tmp_path / "installers"
    assert runner.runs == [(exe, _ARGS)]


def test_registry_toolkit_with_an_empty_process_variable_downloads_nothing(
        tmp_path, recording_console):
    """Check that registry toolkit with an empty process variable downloads nothing."""
    root = _toolkit(tmp_path / "CUDA" / "v12.6")
    downloader, runner = _FakeDownloader(None), _FakeRunner(0)
    environment = _FakeEnvironment({"CUDA_PATH": str(root)})

    assert WindowsCudaLocator(_tools(tmp_path, downloader, runner, environment)).provision(
        _CFG, False)

    assert downloader.fetched == [] and runner.runs == []
    assert pathlib.Path(os.environ["CUDA_PATH"]) == root


def test_both_variables_empty_downloads(tmp_path, recording_console):
    """Check that both variables empty downloads."""
    downloader = _FakeDownloader(None)

    WindowsCudaLocator(_tools(tmp_path, downloader, _FakeRunner(0))).provision(_CFG, False)

    assert len(downloader.fetched) == 1


def test_declined_elevation_warns_and_is_non_fatal(tmp_path, recording_console):
    """Check that declined elevation warns and is non fatal."""
    runner = _FakeRunner(wi.ELEVATION_DECLINED)
    locator = WindowsCudaLocator(_tools(tmp_path, _FakeDownloader(_installer(tmp_path)), runner))

    assert locator.provision(_CFG, False) is True
    assert any("administrator prompt was declined" in w for w in _warnings(recording_console))
    assert "CUDA_PATH" not in os.environ


def test_a_launch_failure_reports_its_own_message(tmp_path, recording_console):
    """Check that a launch failure reports its own message."""
    runner = _FakeRunner(wi.LAUNCH_FAILED, "This command cannot be run: blocked by policy")
    locator = WindowsCudaLocator(_tools(tmp_path, _FakeDownloader(_installer(tmp_path)), runner))

    assert locator.provision(_CFG, False) is True
    warnings = _warnings(recording_console)
    assert any("blocked by policy" in w and "code 1" in w for w in warnings)
    assert not any("declined" in w for w in warnings)


def test_failed_install_warns_with_its_exit_code(tmp_path, recording_console):
    """Check that failed install warns with its exit code."""
    locator = WindowsCudaLocator(
        _tools(tmp_path, _FakeDownloader(_installer(tmp_path)), _FakeRunner(-1)))

    assert locator.provision(_CFG, False) is True
    assert any("exited with code -1" in w for w in _warnings(recording_console))


def test_a_non_zero_exit_that_installed_the_toolkit_reports_success(tmp_path, recording_console):
    """Check that a non zero exit that installed the toolkit reports success."""
    root = tmp_path / "CUDA" / "v12.6"
    environment = _FakeEnvironment({"CUDA_PATH": str(root)})
    runner = _FakeRunner(3010, on_run=lambda: _toolkit(root))
    locator = WindowsCudaLocator(
        _tools(tmp_path, _FakeDownloader(_installer(tmp_path)), runner, environment))

    assert locator.provision(_CFG, False) is True
    assert _warnings(recording_console) == []
    assert any("3010" in s for s in _successes(recording_console))


def test_failed_download_runs_nothing_and_is_non_fatal(tmp_path, recording_console):
    """Check that failed download runs nothing and is non fatal."""
    runner = _FakeRunner(0)

    assert WindowsCudaLocator(_tools(tmp_path, _FakeDownloader(None), runner)).provision(
        _CFG, False)
    assert runner.runs == []
    assert _warnings(recording_console)


@pytest.mark.skipif(os.name != "nt",
                    reason="asserts on a PATH split by os.pathsep, which is ';' only on Windows")
def test_success_refreshes_cuda_path_and_path_and_deletes_the_installer(
        tmp_path, recording_console):
    """Check that success refreshes cuda path and path and deletes the installer."""
    root = tmp_path / "CUDA" / "v12.6"
    exe = _installer(tmp_path)
    environment = _FakeEnvironment({})

    def install():
        """Check that install."""
        _toolkit(root)
        environment.values["CUDA_PATH"] = str(root)
        environment.values["Path"] = os.pathsep.join([str(root / "bin"), r"c:\windows"])

    runner = _FakeRunner(0, on_run=install)
    locator = WindowsCudaLocator(_tools(tmp_path, _FakeDownloader(exe), runner, environment))

    assert locator.provision(_CFG, False) is True
    assert pathlib.Path(os.environ["CUDA_PATH"]) == root
    assert os.environ["PATH"].split(os.pathsep) == [str(root / "bin"), r"C:\Windows"]
    assert locator.locate(_CFG).root == root
    assert _warnings(recording_console) == []
    assert not exe.exists()


def test_dry_run_prints_the_command_and_runs_nothing(tmp_path, recording_console):
    """Check that dry run prints the command and runs nothing."""
    downloader, runner = _FakeDownloader(None), _FakeRunner(0)

    assert WindowsCudaLocator(_tools(tmp_path, downloader, runner)).provision(_CFG, True)

    exe = tmp_path / "installers" / "cuda_12.6.3_windows_network.exe"
    assert _commands(recording_console) == [
        subprocess.list2cmdline(["elevate", str(exe), *_ARGS])]
    assert downloader.fetched == [] and runner.runs == []


def test_present_toolkit_downloads_nothing(tmp_path, monkeypatch, recording_console):
    """Check that present toolkit downloads nothing."""
    monkeypatch.setenv("CUDA_PATH", str(_toolkit(tmp_path / "cuda")))
    downloader, runner = _FakeDownloader(None), _FakeRunner(0)

    assert WindowsCudaLocator(_tools(tmp_path, downloader, runner)).provision(_CFG, False)
    assert downloader.fetched == [] and runner.runs == []


def test_the_elevated_command_maps_only_error_1223_to_declined(tmp_path):
    """Check that the elevated command maps only error 1223 to declined."""
    cmd = wi.PowerShellElevatedRunner().command(tmp_path / "it's.exe", _ARGS)

    assert cmd[:4] == ["powershell", "-NoProfile", "-NonInteractive", "-Command"]
    assert "-Verb RunAs -Wait -PassThru" in cmd[4]
    assert "'-s nvcc_12.6 cudart_12.6 nvml_dev_12.6 -n'" in cmd[4]
    assert "it''s.exe" in cmd[4]
    assert (f"NativeErrorCode -eq {wi.ELEVATION_DECLINED}) "
            f"{{ exit {wi.ELEVATION_DECLINED} }}") in cmd[4]
    assert f"[Console]::Error.WriteLine($_.Exception.Message); exit {wi.LAUNCH_FAILED}" in cmd[4]


# HttpDownloader

def _download_of(payload: bytes) -> wi.InstallerDownload:
    """Describe an installer whose published MD5 is that of *payload*."""
    return wi.InstallerDownload(url="https://invalid.example/a.exe", file_name="a.exe",
                                md5=hashlib.md5(payload).hexdigest())


class _Response:
    """A urlopen stand-in that yields *payload*, then raises *error* when one is given."""

    def __init__(self, payload: bytes, error: Exception | None = None) -> None:
        """Store the payload and the error raised after it."""
        self._chunks = [payload]
        self._error = error

    def __enter__(self):
        """Return self as the context value."""
        return self

    def __exit__(self, *exc) -> None:
        """Close nothing."""

    def read(self, size: int) -> bytes:
        """Return the payload once, then raise the error or signal the end."""
        if self._chunks:
            return self._chunks.pop()
        if self._error:
            raise self._error
        return b""


def test_the_downloader_reuses_a_file_whose_md5_matches(tmp_path, monkeypatch, recording_console):
    """Check that the downloader reuses a file whose md5 matches."""
    (tmp_path / "a.exe").write_bytes(b"abc")
    monkeypatch.setattr(wi.urllib.request, "urlopen",
                        lambda *a, **k: pytest.fail("must not download"))

    assert wi.HttpDownloader().fetch(_download_of(b"abc"), tmp_path) == tmp_path / "a.exe"


def test_a_mismatching_reused_file_is_deleted_and_downloaded_once(tmp_path, monkeypatch,
                                                                  recording_console):
    """Check that a mismatching reused file is deleted and downloaded once."""
    (tmp_path / "a.exe").write_bytes(b"stale")
    calls: list[str] = []

    def urlopen(request, timeout):
        """Check that urlopen."""
        calls.append(request.full_url)
        return _Response(b"good")

    monkeypatch.setattr(wi.urllib.request, "urlopen", urlopen)

    assert wi.HttpDownloader().fetch(_download_of(b"good"), tmp_path) == tmp_path / "a.exe"
    assert (tmp_path / "a.exe").read_bytes() == b"good"
    assert len(calls) == 1
    assert not (tmp_path / "a.exe.part").exists()


def test_a_digest_mismatch_leaves_no_file(tmp_path, monkeypatch, recording_console):
    """Check that a digest mismatch leaves no file."""
    monkeypatch.setattr(wi.urllib.request, "urlopen", lambda *a, **k: _Response(b"evil"))

    assert wi.HttpDownloader().fetch(_download_of(b"good"), tmp_path) is None
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("error", [
    http.client.IncompleteRead(b"partial"),
    ValueError("bad url"),
    OSError("connection reset"),
])
def test_a_download_error_is_caught_and_leaves_no_part_file(tmp_path, monkeypatch,
                                                            recording_console, error):
    """Check that a download error is caught and leaves no part file."""
    monkeypatch.setattr(wi.urllib.request, "urlopen",
                        lambda *a, **k: _Response(b"half", error))

    assert wi.HttpDownloader().fetch(_download_of(b"good"), tmp_path) is None
    assert list(tmp_path.iterdir()) == []
    assert _warnings(recording_console)


def test_an_unreadable_reused_file_is_caught(tmp_path, monkeypatch, recording_console):
    """Check that an unreadable reused file is caught."""
    (tmp_path / "a.exe").write_bytes(b"abc")

    def locked(path):
        """Check that locked."""
        raise PermissionError("locked")

    monkeypatch.setattr(wi, "_md5_of", locked)

    assert wi.HttpDownloader().fetch(_download_of(b"abc"), tmp_path) is None
    assert any("locked" in w for w in _warnings(recording_console))


@pytest.mark.skipif(os.name != "nt",
                    reason="asserts on a PATH split by os.pathsep, which is ';' only on Windows")
def test_prepend_machine_path_adds_only_new_entries(monkeypatch):
    """Check that prepend machine path adds only new entries."""
    monkeypatch.setenv("PATH", os.pathsep.join([r"C:\Windows", r"C:\Tools"]))
    environment = _FakeEnvironment({"Path": os.pathsep.join([r"c:\windows", r"C:\CUDA\bin"])})

    wi.prepend_machine_path(environment)

    assert os.environ["PATH"].split(os.pathsep) == [r"C:\CUDA\bin", r"C:\Windows", r"C:\Tools"]


# GPU detection

@pytest.mark.parametrize("names, vendor", [
    ("nvidia geforce rtx 3080 ti\namd radeon(tm) graphics", "nvidia"),
    ("intel(r) uhd graphics 630", "intel"),
    ("amd radeon(tm) graphics", "amd"),
    ("amd radeon 780m graphics", "amd"),
    ("amd radeon rx 7900 xt\nintel(r) uhd graphics 770", "amd"),
    ("intel(r) uhd graphics 770\namd radeon rx 7900 xt", "amd"),
    ("vga compatible controller: advanced micro devices, inc. [amd/ati] barcelo", "amd"),
    ("vga compatible controller: intel corporation dg2 [arc a770]", "intel"),
    ("microsoft basic display adapter", "none"),
    ("", "none"),
])
def test_display_adapters_prefer_a_discrete_vendor_and_fall_back_to_an_integrated_one(
        names, vendor):
    """Check that display adapters prefer a discrete vendor and fall back to an integrated one."""
    assert probe.classify_display_adapters(names) == vendor


@pytest.mark.parametrize("line, integrated", [
    ("00:02.0 vga compatible controller: intel corporation alderlake-s gt1", True),
    ("intel(r) uhd graphics (alder lake)", True),
    ("amd radeon(tm) graphics", True),
    ("amd radeon rx 6800", False),
    ("intel(r) arc(tm) a770 graphics", False),
    ("nvidia geforce rtx 3080 ti", False),
])
def test_integrated_matching_ignores_spaces_and_hyphens(line, integrated):
    """Check that integrated matching ignores spaces and hyphens."""
    assert probe.is_integrated_adapter(line) is integrated


def test_windows_detection_reads_the_video_controllers(monkeypatch):
    """Check that windows detection reads the video controllers."""
    monkeypatch.setattr(probe.shutil, "which", lambda name: None)
    monkeypatch.setattr(probe.sys, "platform", "win32")
    monkeypatch.setattr(probe, "_windows_display_adapters", lambda: "nvidia geforce gtx 1080")

    assert probe.detect_gpu_vendor() == "nvidia"


def test_linux_detection_reads_lspci(monkeypatch):
    """Check that linux detection reads lspci."""
    monkeypatch.setattr(probe.shutil, "which", lambda name: None)
    monkeypatch.setattr(probe.sys, "platform", "linux")
    monkeypatch.setattr(probe, "_linux_display_adapters",
                        lambda: "01:00.0 vga compatible controller: advanced micro devices "
                                "navi 21 [radeon rx 6800]")

    assert probe.detect_gpu_vendor() == "amd"
