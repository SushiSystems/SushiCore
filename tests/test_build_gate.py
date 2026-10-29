# test_build_gate.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The memory gate admits an edge only when its measured peak fits, in arrival order."""

from __future__ import annotations

import struct
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


def test_a_cache_setting_the_environment_makes_is_kept(tmp_path, monkeypatch):
    monkeypatch.setenv("CCACHE_DIR", "D:/ci/ccache")
    _, env = build_gate.cached(["clang++", "-c", "a.cpp"], "host_compile", "ccache", tmp_path / "g")
    assert env["CCACHE_DIR"] == "D:/ci/ccache" and env["CCACHE_COMPILERCHECK"] == "content"


def test_only_a_host_compile_runs_through_the_compiler_cache(tmp_path, monkeypatch):
    """Checks a device object never comes from the cache, where a stale one loses its kernels."""
    monkeypatch.delenv("CCACHE_DIR", raising=False)
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


def test_only_a_compile_of_a_requested_unit_is_traced():
    requested = {"d:/src/a.cpp", "b.cpp"}
    assert build_gate.wants_time_trace("device_compile", "d:/src/a.cpp", requested)
    assert build_gate.wants_time_trace("host_compile", "b.cpp -O0", requested)
    assert not build_gate.wants_time_trace("host_compile", "c.cpp -O0", requested)
    assert not build_gate.wants_time_trace("host_link", "b.cpp", requested)
    assert not build_gate.wants_time_trace("host_compile", "b.cpp", set())


def test_a_requested_compile_runs_with_the_time_trace_flag_and_skips_the_cache(tmp_path, monkeypatch):
    state = tmp_path / "gate"
    state.mkdir()
    (state / build_gate.K_TIME_TRACE).write_text("a.cpp\n", encoding="utf-8")
    seen: list[list[str]] = []
    monkeypatch.setattr(build_gate.subprocess, "call", lambda command, env=None: seen.append(command) or 0)
    build_gate.run(state, ["clang++", "-O0", "-c", "a.cpp"], cache="ccache")
    build_gate.run(state, ["clang++", "-O0", "-c", "b.cpp"], cache="ccache")
    assert seen[0] == ["clang++", "-O0", "-c", "a.cpp", "-ftime-trace"]
    assert seen[1][0] == "ccache" and "-ftime-trace" not in seen[1]


@pytest.mark.parametrize("name", [
    b"??$parallel_for@V<lambda_1>@@@handler@_V1@sycl@@QEAAXV?$range@$00@12@@Z",
    b"??$single_task@VKernel@@V<lambda_2>@@@handler@_V1@sycl@@QEAAXV<lambda_2>@@@Z",
    b"_ZN4sycl3_V17handler12parallel_forI6KernelLi1EZ4stepvEUlNS0_4itemILi1ELb1EEEE_EEvNS0_5rangeIXT0_EEET1_",
])
def test_a_host_object_that_instantiates_a_kernel_submission_is_found(tmp_path, name):
    obj = tmp_path / "a.obj"
    obj.write_bytes(b"\x00junk\x00" + name + b"\x00tail")
    assert build_gate.kernel_submission_in(obj)


def test_a_host_object_without_one_passes(tmp_path):
    obj = tmp_path / "a.obj"
    obj.write_bytes(b"\x00?submit_impl@queue@_V1@sycl@@\x00?host_task@handler@_V1@sycl@@\x00")
    assert build_gate.kernel_submission_in(obj) == ""
    assert build_gate.kernel_submission_in(tmp_path / "missing.obj") == ""


K_ITANIUM_SINGLE_TASK = b"_ZN4sycl3_V17handler11single_taskI6KernelZ4stepvEUlvE_EEvT0_"


def _elf_object(symbol: bytes, shndx: int, debug: bytes = b"") -> bytes:
    """Returns an ELF64 object whose symbol table holds *symbol* in section *shndx*."""
    strtab = b"\x00" + symbol + b"\x00"
    symtab = bytes(24) + struct.pack("<IBBHQQ", 1, 0x12, 0, shndx, 0, 0)
    blobs = [strtab, symtab, debug]
    offset = 64
    headers = [bytes(64)]
    for kind, blob, link, entsize in ((3, strtab, 0, 0), (2, symtab, 1, 24), (1, debug, 0, 0)):
        headers.append(struct.pack("<IIQQQQIIQQ", 0, kind, 0, 0, offset, len(blob), link, 0, 1,
                                   entsize))
        offset += len(blob)
    ident = b"\x7fELF\x02\x01\x01" + bytes(9)
    head = ident + struct.pack("<HHIQQQIHHHHHH", 1, 62, 1, 0, 0, offset, 0, 64, 0, 0, 64, 4, 0)
    return head + b"".join(blobs) + b"".join(headers)


def _coff_object(symbol: bytes, section: int) -> bytes:
    """Returns an AMD64 COFF object whose one symbol names *symbol* in *section*."""
    record = struct.pack("<IIIhHBB", 0, 4, 0, section, 0x20, 2, 0)
    strings = struct.pack("<I", 4 + len(symbol) + 1) + symbol + b"\x00"
    return struct.pack("<HHIIIHH", 0x8664, 0, 0, 20, 1, 0, 0) + record + strings


def test_an_elf_object_that_defines_a_kernel_submission_is_found(tmp_path):
    obj = tmp_path / "a.o"
    obj.write_bytes(_elf_object(K_ITANIUM_SINGLE_TASK, shndx=2))
    assert build_gate.kernel_submission_in(obj)


def test_an_elf_object_whose_debug_information_names_a_submission_passes(tmp_path):
    obj = tmp_path / "a.o"
    obj.write_bytes(_elf_object(b"_Z4stepv", shndx=2, debug=K_ITANIUM_SINGLE_TASK + b"\x00"))
    assert build_gate.kernel_submission_in(obj) == ""


def test_an_elf_object_that_only_references_a_submission_passes(tmp_path):
    obj = tmp_path / "a.o"
    obj.write_bytes(_elf_object(K_ITANIUM_SINGLE_TASK, shndx=0))
    assert build_gate.kernel_submission_in(obj) == ""


def test_a_coff_object_is_judged_by_the_symbols_it_defines(tmp_path):
    name = b"??$single_task@VKernel@@V<lambda_2>@@@handler@_V1@sycl@@QEAAXV<lambda_2>@@@Z"
    defined, referenced = tmp_path / "a.obj", tmp_path / "b.obj"
    defined.write_bytes(_coff_object(name, section=1))
    referenced.write_bytes(_coff_object(name, section=0))
    assert build_gate.kernel_submission_in(defined)
    assert build_gate.kernel_submission_in(referenced) == ""


def test_a_host_compile_that_instantiates_a_kernel_fails_and_loses_its_object(tmp_path):
    state = tmp_path / "gate"
    obj = tmp_path / "a.obj"
    writer = (f"open(r'{obj}', 'wb').write(b'??$parallel_for@V<l>@@@handler@_V1@sycl@@Q')")
    code = build_gate.main(["gate", str(state), "--", sys.executable, "-c", writer,
                            "-o", str(obj), "-c", "a.cpp"])
    assert code == 1 and not obj.exists()
