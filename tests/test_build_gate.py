# test_build_gate.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The memory gate admits an edge only when its measured peak fits, in arrival order."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from sushicore import build_gate

pytestmark = pytest.mark.small


@pytest.fixture
def everyone_alive(monkeypatch):
    """Makes every fake pid a running process."""
    monkeypatch.setattr(build_gate, "alive", lambda pid: True)


def _idle_ledger(free_mb: int) -> dict:
    ledger: dict = {}
    assert build_gate.admit(ledger, 1, 10, free_mb, 0.0)
    ledger["running"].clear()
    return ledger


def test_an_edge_that_fits_is_admitted_and_reserved(everyone_alive):
    ledger = _idle_ledger(10000)
    assert ledger["budget"] == 10000 - build_gate.K_RESERVE_MB
    assert build_gate.admit(ledger, 2, 3000, 10000, 1.0)
    assert ledger["running"] == {"2": 3000}


def test_an_edge_that_does_not_fit_waits_until_the_running_ones_end(everyone_alive, monkeypatch):
    ledger = _idle_ledger(10000)
    assert build_gate.admit(ledger, 2, 8000, 10000, 1.0)
    assert not build_gate.admit(ledger, 3, 8000, 10000, 1.0)
    monkeypatch.setattr(build_gate, "alive", lambda pid: pid != 2)
    assert build_gate.admit(ledger, 3, 8000, 10000, 2.0)


def test_an_edge_alone_is_admitted_whatever_its_peak(everyone_alive):
    ledger: dict = {}
    assert build_gate.admit(ledger, 1, 50000, 4000, 0.0)


def test_a_light_edge_passes_a_waiting_heavy_head_only_inside_the_backfill_window(everyone_alive):
    ledger = _idle_ledger(10000)
    assert build_gate.admit(ledger, 2, 6000, 10000, 0.0)
    assert not build_gate.admit(ledger, 3, 8000, 10000, 0.0)
    assert build_gate.admit(ledger, 4, 500, 10000, 1.0)
    late = build_gate.K_BACKFILL_WINDOW + 1.0
    assert not build_gate.admit(ledger, 5, 500, 10000, late)


def test_nothing_is_admitted_beside_running_work_when_free_memory_is_under_the_reserve(everyone_alive):
    ledger = _idle_ledger(10000)
    assert build_gate.admit(ledger, 2, 500, 10000, 0.0)
    assert not build_gate.admit(ledger, 3, 500, build_gate.K_RESERVE_MB - 1, 0.0)


def test_edges_are_told_apart_and_keyed_by_source_or_output():
    compile_device = ["clang++", "-fsycl", "-o", "a.obj", "-c", r"D:\Src\A.cpp"]
    assert build_gate.edge_of(compile_device) == ("device_compile", "d:/src/a.cpp")
    compile_debug = ["clang++", "-O0", "-o", "a.obj", "-c", "a.cpp"]
    assert build_gate.edge_of(compile_debug) == ("host_compile", "a.cpp -O0")
    link_host = ["lld-link", "/out:bin\\T.exe", "a.obj"]
    assert build_gate.edge_of(link_host) == ("host_link", "bin/t.exe")
    link_device = ["clang++", "-fsycl", "a.obj", "-o", "t.exe"]
    assert build_gate.edge_of(link_device) == ("device_link", "t.exe")


def test_a_measured_unit_is_reserved_at_its_own_peak():
    peaks = {"a.cpp": 700, "@device_compile": 9000}
    assert build_gate.expected_peak(peaks, "device_compile", "a.cpp") == 700


def test_a_new_unit_is_reserved_at_the_larger_of_its_kinds_default_and_largest_peak():
    """Checks light units measured first never lower the guess for the heavy ones not seen yet."""
    default = build_gate.K_DEFAULT_PEAK_MB["device_compile"]
    assert build_gate.expected_peak({"@device_compile": 251}, "device_compile", "b.cpp") == default
    assert build_gate.expected_peak({"@device_compile": default + 1}, "device_compile", "b.cpp") == default + 1
    assert build_gate.expected_peak({}, "host_link", "t.exe") == build_gate.K_DEFAULT_PEAK_MB["host_link"]


def test_a_gated_command_runs_returns_its_code_and_leaves_the_ledger_empty(tmp_path):
    state = tmp_path / "gate"
    code = build_gate.main(["gate", str(state), "--", sys.executable, "-c", "raise SystemExit(3)"])
    assert code == 3
    ledger = build_gate._read(state / build_gate.K_LEDGER, {})
    assert ledger["running"] == {} and ledger["queue"] == []
    peaks = build_gate._read(state / build_gate.K_PEAKS, {})
    if sys.platform == "win32":
        assert peaks["@host_compile"] > 0


def test_memory_freed_by_another_program_during_the_build_is_used(everyone_alive):
    ledger = _idle_ledger(4000)
    assert build_gate.admit(ledger, 2, 2000, 4000, 0.0)
    assert not build_gate.admit(ledger, 3, 2000, 4000, 0.0)
    assert build_gate.admit(ledger, 3, 2000, 12000, 1.0)


def test_a_stopped_gate_fails_the_edge_without_running_it(tmp_path):
    state = tmp_path / "gate"
    state.mkdir()
    (state / build_gate.K_STOP).touch()
    marker = tmp_path / "ran"
    code = build_gate.main(["gate", str(state), "--", sys.executable, "-c",
                            f"open(r'{marker}', 'w').close()"])
    assert code == 1 and not marker.exists()


def test_only_a_host_compile_runs_through_the_compiler_cache(tmp_path):
    """Checks a device object never comes from the cache, where a stale one loses its kernels."""
    state = tmp_path / "build_gate"
    host = ["clang++", "-c", "a.cpp"]
    command, env = build_gate.cached(host, "host_compile", "ccache", state)
    assert command == ["ccache", *host]
    assert env["CCACHE_DIR"] == str(tmp_path / "ccache") and env["CCACHE_COMPILERCHECK"] == "content"
    for kind in ("device_compile", "host_link", "device_link"):
        assert build_gate.cached(host, kind, "ccache", state) == (host, None)
    assert build_gate.cached(host, "host_compile", "", state) == (host, None)


def test_a_cache_option_reaches_the_gated_command(tmp_path, monkeypatch):
    seen = {}
    monkeypatch.setattr(build_gate, "run", lambda state, command, cache="": seen.update(
        state=state, command=command, cache=cache) or 0)
    assert build_gate.main(["gate", "s", "--cache", "ccache", "--", "clang++", "-c", "a.cpp"]) == 0
    assert seen == {"state": Path("s"), "command": ["clang++", "-c", "a.cpp"], "cache": "ccache"}
    assert build_gate.main(["gate", "s", "--cache"]) == 2
