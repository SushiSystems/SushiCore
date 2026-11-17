# test_probe.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for what the machine probes read: adapters, Visual Studio, toolchains and binaries."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.proc_memory import RecordingRunner
from sushicore.provision import probe
from sushicore.provision.host import PosixHost, WindowsHost
from sushicore.provision.config import ProvisionSettings


_CLANG = Path("bin") / "clang++"
K_ROOT = Path("/machine/root")
K_LEGACY = Path("/machine/legacy")


@pytest.mark.small
def test_classify_prefers_a_discrete_adapter():
    """Check that classification prefers a discrete adapter."""
    adapters = "Intel(R) UHD Graphics 770\nNVIDIA GeForce RTX 4070\n"
    assert probe.classify_display_adapters(adapters) == "nvidia"


@pytest.mark.small
def test_integrated_only_falls_back_to_its_vendor():
    """Check that integrated-only falls back to its vendor."""
    assert probe.classify_display_adapters("Intel(R) UHD Graphics 770\n") == "intel"


@pytest.mark.small
def test_an_intel_arc_a_series_line_is_discrete_not_integrated():
    """Check that an Intel Arc A-series adapter is not reported as integrated."""
    assert probe.is_integrated_adapter("Intel(R) Arc(TM) A770 Graphics") is False


@pytest.mark.medium
def test_binary_works_rejects_a_missing_command():
    """Check that binary_works rejects a missing command."""
    assert probe.binary_works("sushi-no-such-binary-xyz") is False


@pytest.mark.small
def test_find_vcvars_is_none_off_windows():
    """Check that no Visual Studio script is looked for off Windows."""
    assert probe.find_vcvars(host=PosixHost(), vswhere=lambda: Path("never")) is None


def _vs_tree(root, year, edition):
    """Create a vcvars64.bat of *year* and *edition* below *root* and return it."""
    bat = root / "Microsoft Visual Studio" / year / edition / "VC" / "Auxiliary" / "Build"
    bat.mkdir(parents=True)
    (bat / "vcvars64.bat").write_text("")
    return bat / "vcvars64.bat"


@pytest.mark.medium
def test_find_vcvars_scans_the_newest_year_first(tmp_path):
    """Check that the disk scan takes the newest year's install."""
    _vs_tree(tmp_path, "2019", "Community")
    newest = _vs_tree(tmp_path, "2026", "BuildTools")
    found = probe.find_vcvars(host=WindowsHost(), vswhere=lambda: None, program_files=[tmp_path])
    assert found == newest


@pytest.mark.small
def test_find_vcvars_prefers_vswhere():
    """Check that the install vswhere reports wins over the disk scan."""
    hit = Path("/machine/vcvars64.bat")
    assert probe.find_vcvars(host=WindowsHost(), vswhere=lambda: hit, program_files=[]) == hit


@pytest.mark.small
def test_find_vcvars_is_none_when_nothing_is_installed():
    """Check that no vswhere answer and no scanned folder give None."""
    assert probe.find_vcvars(host=WindowsHost(), vswhere=lambda: None, program_files=[]) is None


def _windows_cfg():
    """Return a Windows configuration naming no tool path."""
    return ProvisionSettings(platform="windows")


@pytest.mark.small
@pytest.mark.parametrize(("glob_hit", "found", "expected"), [
    ("C:/VS/2022/x.bat", None, "C:/VS/2022/x.bat"),
    ("", Path("/machine/vcvars64.bat"), str(Path("/machine/vcvars64.bat"))),
], ids=["the 2022 glob comes first", "find_vcvars is the fallback"])
def test_resolve_windows_takes_the_glob_first_and_find_vcvars_second(glob_hit, found, expected):
    """Check the order in which the Visual Studio script is looked for."""
    values = probe._resolve_windows(_windows_cfg(), first_glob=lambda patterns: glob_hit,
                                    vcvars_finder=lambda: found)
    assert values["vs_vcvars"] == expected


def _bundle(root):
    """Create an llvm-sycl bundle holding a clang++ under *root* and return the file."""
    exe = root / "toolchains" / "llvm-sycl" / _CLANG
    exe.parent.mkdir(parents=True)
    exe.write_text("")
    return exe


@pytest.mark.small
@pytest.mark.parametrize(("held", "expected"), [
    ({K_ROOT / "toolchains" / "llvm-sycl" / _CLANG, K_LEGACY / "toolchains" / "llvm-sycl" / _CLANG},
     K_ROOT / "toolchains" / "llvm-sycl" / _CLANG),
    ({K_LEGACY / "toolchains" / "llvm-sycl" / _CLANG},
     K_LEGACY / "toolchains" / "llvm-sycl" / _CLANG),
    (set(), None),
], ids=["the current root first", "a legacy root as the fallback", "no root holds it"])
def test_installed_toolchain_returns_the_first_root_holding_the_file(held, expected):
    """Check that the first root holding the file wins, and that none gives None."""
    found = probe.installed_toolchain("llvm-sycl", _CLANG, roots=[K_ROOT, K_LEGACY],
                                      is_file=lambda path: path in held)
    assert found == expected


@pytest.mark.medium
def test_discovery_records_a_legacy_bundle(provision_home, tmp_path, monkeypatch):
    """Check that a bundle in a legacy root reaches the local config as llvm_root."""
    legacy = tmp_path / "legacy"
    monkeypatch.setenv("SUSHISTACK_DEPS_DIR", str(legacy))
    _bundle(legacy)
    values = probe.resolve_local_config(ProvisionSettings(platform="linux"))
    assert values["llvm_root"] == str((legacy / "toolchains" / "llvm-sycl").resolve())


def _runner() -> RecordingRunner:
    """Return a runner that records commands and starts no process."""
    return RecordingRunner(RecordingConsole())


def _probe_records(caplog, level: str) -> list[str]:
    """Return the messages the provision logger recorded at *level*."""
    return [r.getMessage() for r in caplog.records
            if r.name.startswith("sushicore.provision") and r.levelname == level]


@pytest.mark.small
def test_a_missing_lspci_is_recorded(caplog):
    """Check that an lspci that cannot start yields no adapters and one warning."""
    with caplog.at_level("WARNING", logger="sushicore.provision"):
        assert PosixHost().display_adapters(_runner().script_missing()) == ""
    assert len(_probe_records(caplog, "WARNING")) == 1
    assert "lspci" in _probe_records(caplog, "WARNING")[0]


@pytest.mark.small
def test_lspci_display_lines_are_kept_in_lower_case():
    """Check that only the display-controller lines of lspci come back, lower-cased."""
    runner = _runner().script(0, ("00:02.0 VGA compatible controller: Intel", "00:1f.0 ISA bridge"))
    assert PosixHost().display_adapters(runner) == "00:02.0 vga compatible controller: intel"


@pytest.mark.small
def test_a_video_controller_query_that_times_out_is_recorded(caplog):
    """Check that a PowerShell query that times out yields no adapters and one warning."""
    with caplog.at_level("WARNING", logger="sushicore.provision"):
        assert WindowsHost().display_adapters(_runner().script_timeout()) == ""
    assert len(_probe_records(caplog, "WARNING")) == 1
    assert "timed out" in _probe_records(caplog, "WARNING")[0]


@pytest.mark.small
def test_the_video_controller_names_come_back_in_lower_case():
    """Check that the PowerShell output is lower-cased."""
    assert WindowsHost().display_adapters(_runner().script(0, ("NVIDIA GeForce",))) == (
        "nvidia geforce\n")


@pytest.mark.small
def test_binary_works_is_true_when_version_exits_zero():
    """Check that --version exiting zero is enough, with no second probe."""
    runner = _runner().script(0)
    assert probe.binary_works("cmake", runner) is True
    assert [c.argv for c in runner.commands] == [("cmake", "--version")]


@pytest.mark.small
def test_binary_works_falls_back_to_the_single_dash_flag():
    """Check that a tool that rejects --version is tried with -version."""
    runner = _runner().script(2).script(0)
    assert probe.binary_works("ninja", runner) is True
    assert [c.argv for c in runner.commands] == [("ninja", "--version"), ("ninja", "-version")]


@pytest.mark.small
def test_binary_works_is_false_when_both_flags_exit_non_zero():
    """Check that a tool that rejects both flags does not work."""
    assert probe.binary_works("tool", _runner().script(2).script(2)) is False


@pytest.mark.small
def test_binary_works_records_why_a_command_did_not_run(caplog):
    """Check that binary_works logs the reason behind a False answer."""
    with caplog.at_level("DEBUG", logger="sushicore.provision"):
        assert probe.binary_works("cmake", _runner().script_missing()) is False
    assert len(_probe_records(caplog, "DEBUG")) == 1
    assert "cmake" in _probe_records(caplog, "DEBUG")[0]


def _fake_vswhere(tmp_path):
    """Put a vswhere.exe file where the probe looks and return the folder holding it."""
    vswhere = tmp_path / "Microsoft Visual Studio" / "Installer" / "vswhere.exe"
    vswhere.parent.mkdir(parents=True)
    vswhere.write_text("")
    return tmp_path


@pytest.mark.medium
@pytest.mark.parametrize(("runner", "logged"), [
    (RecordingRunner(RecordingConsole()).script_missing(), "vswhere did not run (Executable not found"),
    (RecordingRunner(RecordingConsole()).script(3), "vswhere exited with status 3"),
], ids=["did not run", "exited non-zero"])
def test_find_vcvars_logs_a_vswhere_that_failed(tmp_path, caplog, runner, logged):
    """Check that a vswhere that cannot start or exits non-zero is recorded and finds nothing."""
    program_files = str(_fake_vswhere(tmp_path))
    with caplog.at_level("WARNING", logger=probe.__name__):
        found = probe.find_vcvars(
            host=WindowsHost(), vswhere=lambda: probe._vcvars_from_vswhere(program_files, runner),
            program_files=[])
    assert found is None
    assert logged in caplog.text
