# test_probe.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for what the toolchain probe reads: installed toolchains and runnable binaries."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.proc_memory import RecordingRunner
from sushicore.provision import probe
from sushicore.provision.config import ProvisionSettings


_CLANG = Path("bin") / "clang++"
K_ROOT = Path("/machine/root")
K_LEGACY = Path("/machine/legacy")


@pytest.mark.medium
def test_binary_works_rejects_a_missing_command():
    """Check that binary_works rejects a missing command."""
    assert probe.binary_works("sushi-no-such-binary-xyz") is False


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
