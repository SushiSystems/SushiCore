# test_build_gate.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The memory gate admits an edge only when its measured peak fits, in arrival order."""

from __future__ import annotations

import struct
import subprocess
import sys
from pathlib import Path

import pytest

from sushicore import build_gate

K_STATE = Path("tree") / "build_gate"

K_DEVICE_DEFAULT = build_gate.K_DEFAULT_PEAK_MB["device_compile"]
K_FLOOR = int(build_gate.K_FLOOR_SHARE * K_DEVICE_DEFAULT)
K_FEW = build_gate.K_ENOUGH_UNITS - 1
K_ENOUGH = build_gate.K_ENOUGH_UNITS


def _all_alive(pid: int) -> bool:
    """Make every fake pid a running process."""
    return True


def _all_alive_but_two(pid: int) -> bool:
    """Make every fake pid but 2 a running process."""
    return pid != 2


def _idle_ledger(free_mb: int) -> dict:
    """Return a ledger whose budget the first edge set from *free_mb*, with nothing running."""
    ledger: dict = {}
    build_gate.admit(ledger, 1, 10, free_mb, 0.0, is_alive=_all_alive)
    ledger["running"].clear()
    return ledger


def _busy_ledger() -> dict:
    """Return a ledger in which edge 2 runs with a reservation of 8000 of 10000 free."""
    ledger = _idle_ledger(10000)
    build_gate.admit(ledger, 2, 8000, 10000, 1.0, is_alive=_all_alive)
    return ledger


def _ledger_with_a_heavy_head_waiting() -> dict:
    """Return a ledger in which edge 2 runs and the heavy edge 3 heads the queue since time 0."""
    ledger = _idle_ledger(10000)
    build_gate.admit(ledger, 2, 6000, 10000, 0.0, is_alive=_all_alive)
    build_gate.admit(ledger, 3, 8000, 10000, 0.0, is_alive=_all_alive)
    return ledger


def _measured(kind, units, largest):
    """Returns a peaks table in which *units* units of *kind* are measured, the heaviest at *largest*."""
    peaks = {f"u{index}.cpp": 100 for index in range(units)}
    peaks[f"u{units}.cpp"] = largest
    peaks["@" + kind] = largest
    peaks["#" + kind] = units + 1
    return peaks


def _recorded_peaks() -> dict:
    """Return the peaks after unit a.cpp measured at 300 and 500 and unit b.cpp at 200."""
    peaks: dict = {}
    build_gate.record_peak(peaks, "host_compile", "a.cpp", 300)
    build_gate.record_peak(peaks, "host_compile", "a.cpp", 500)
    build_gate.record_peak(peaks, "host_compile", "b.cpp", 200)
    return peaks


@pytest.mark.small
def test_an_edge_that_fits_is_admitted_and_reserved():
    ledger = _idle_ledger(10000)
    assert ledger["budget"] == 10000 - build_gate.K_RESERVE_MB
    assert build_gate.admit(ledger, 2, 3000, 10000, 1.0, is_alive=_all_alive)
    assert ledger["running"] == {"2": 3000}


@pytest.mark.small
def test_an_edge_that_does_not_fit_waits_while_the_running_ones_run():
    ledger = _busy_ledger()
    assert not build_gate.admit(ledger, 3, 8000, 10000, 1.0, is_alive=_all_alive)


@pytest.mark.small
def test_a_waiting_edge_is_admitted_when_the_running_ones_end():
    ledger = _busy_ledger()
    assert build_gate.admit(ledger, 3, 8000, 10000, 2.0, is_alive=_all_alive_but_two)


@pytest.mark.small
def test_an_edge_alone_is_admitted_whatever_its_peak():
    ledger: dict = {}
    assert build_gate.admit(ledger, 1, 50000, 4000, 0.0)


@pytest.mark.small
def test_a_light_edge_passes_a_waiting_heavy_head_inside_the_backfill_window():
    ledger = _ledger_with_a_heavy_head_waiting()
    assert build_gate.admit(ledger, 4, 500, 10000, 1.0, is_alive=_all_alive)


@pytest.mark.small
def test_a_light_edge_is_refused_behind_a_heavy_head_that_waited_past_the_backfill_window():
    ledger = _ledger_with_a_heavy_head_waiting()
    late = build_gate.K_BACKFILL_WINDOW + 1.0
    assert not build_gate.admit(ledger, 5, 500, 10000, late, is_alive=_all_alive)


@pytest.mark.small
def test_nothing_is_admitted_beside_running_work_when_free_memory_is_under_the_reserve():
    ledger = _idle_ledger(10000)
    build_gate.admit(ledger, 2, 500, 10000, 0.0, is_alive=_all_alive)
    assert not build_gate.admit(ledger, 3, 500, build_gate.K_RESERVE_MB - 1, 0.0, is_alive=_all_alive)


@pytest.mark.small
@pytest.mark.parametrize(("command", "expected"), [
    (["clang++", "-fsycl", "-o", "a.obj", "-c", r"D:\Src\A.cpp"], ("device_compile", "d:/src/a.cpp")),
    (["clang++", "-O0", "-o", "a.obj", "-c", "a.cpp"], ("host_compile", "a.cpp -O0")),
    (["lld-link", "/out:bin\\T.exe", "a.obj"], ("host_link", "bin/t.exe")),
    (["clang++", "-fsycl", "a.obj", "-o", "t.exe"], ("device_link", "t.exe")),
])
def test_edges_are_told_apart_and_keyed_by_source_or_output(command, expected):
    assert build_gate.edge_of(command) == expected


@pytest.mark.small
def test_a_unit_measured_before_keeps_its_own_peak_whatever_the_kind_shows():
    peaks = _measured("device_compile", K_ENOUGH, 9000)
    assert build_gate.expected_peak({**peaks, "a.cpp": 700}, "device_compile", "a.cpp") == 700


@pytest.mark.small
@pytest.mark.parametrize(("peaks", "kind", "expected"), [
    (_measured("device_compile", K_FEW - 1, 251), "device_compile", K_DEVICE_DEFAULT),
    ({"@device_compile": K_DEVICE_DEFAULT + 1}, "device_compile", K_DEVICE_DEFAULT + 1),
    ({}, "host_link", build_gate.K_DEFAULT_PEAK_MB["host_link"]),
])
def test_a_new_unit_is_reserved_at_the_larger_of_its_kinds_default_and_largest_peak_while_few_are_measured(
    peaks, kind, expected,
):
    """Checks light units measured first never lower the guess for the heavy ones not seen yet."""
    assert build_gate.expected_peak(peaks, kind, "new.cpp") == expected


@pytest.mark.small
@pytest.mark.parametrize(("largest", "expected"), [
    (393, K_FLOOR),
    (K_FLOOR, int(build_gate.K_HEADROOM * K_FLOOR)),
])
def test_a_well_measured_kind_reserves_headroom_over_its_largest_peak_not_the_default(largest, expected):
    peaks = _measured("device_compile", K_ENOUGH, largest)
    assert build_gate.expected_peak(peaks, "device_compile", "new.cpp") == expected


@pytest.mark.small
@pytest.mark.parametrize(("largest", "expected"), [
    (K_DEVICE_DEFAULT - 1, K_DEVICE_DEFAULT),
    (K_DEVICE_DEFAULT + 500, K_DEVICE_DEFAULT + 500),
])
def test_headroom_never_exceeds_the_default_and_never_falls_below_the_largest_peak(largest, expected):
    peaks = _measured("device_compile", K_ENOUGH, largest)
    assert build_gate.expected_peak(peaks, "device_compile", "n.cpp") == expected


@pytest.mark.small
def test_a_peak_counts_its_unit_once():
    assert _recorded_peaks()["#host_compile"] == 2


@pytest.mark.small
def test_a_peak_keeps_the_largest_for_its_unit_and_its_kind():
    peaks = _recorded_peaks()
    assert (peaks["a.cpp"], peaks["b.cpp"], peaks["@host_compile"]) == (500, 200, 500)


@pytest.mark.medium
def test_a_gated_command_returns_its_code_and_leaves_the_ledger_empty(tmp_path):
    state = tmp_path / "gate"
    code = build_gate.main(["gate", str(state), "--", sys.executable, "-c", "raise SystemExit(3)"])
    ledger = build_gate._read(state / build_gate.K_LEDGER, {})
    assert (code, ledger["running"], ledger["queue"]) == (3, {}, [])


@pytest.mark.medium
@pytest.mark.skipif(sys.platform != "win32", reason="the peak of a job object is read on Windows")
def test_a_gated_command_records_a_peak(tmp_path):
    state = tmp_path / "gate"
    build_gate.main(["gate", str(state), "--", sys.executable, "-c", "raise SystemExit(0)"])
    assert build_gate._read(state / build_gate.K_PEAKS, {})["@host_compile"] > 0


@pytest.mark.small
def test_memory_freed_by_another_program_during_the_build_is_used():
    ledger = _idle_ledger(4000)
    build_gate.admit(ledger, 2, 2000, 4000, 0.0, is_alive=_all_alive)
    build_gate.admit(ledger, 3, 2000, 4000, 0.0, is_alive=_all_alive)
    assert build_gate.admit(ledger, 3, 2000, 12000, 1.0, is_alive=_all_alive)


@pytest.mark.medium
def test_a_stopped_gate_fails_the_edge_without_running_it(tmp_path):
    state = tmp_path / "gate"
    state.mkdir()
    (state / build_gate.K_STOP).touch()
    marker = tmp_path / "ran"
    code = build_gate.main(["gate", str(state), "--", sys.executable, "-c",
                            f"open(r'{marker}', 'w').close()"])
    assert code == 1 and not marker.exists()


@pytest.mark.small
def test_a_cache_setting_the_environment_makes_is_kept():
    _, env = build_gate.cached(["clang++", "-c", "a.cpp"], "host_compile", "ccache", K_STATE,
                               environ={"CCACHE_DIR": "D:/ci/ccache"})
    assert env["CCACHE_DIR"] == "D:/ci/ccache" and env["CCACHE_COMPILERCHECK"] == "content"


@pytest.mark.small
def test_a_host_compile_runs_through_the_compiler_cache_beside_the_state_folder():
    host = ["clang++", "-c", "a.cpp"]
    command, env = build_gate.cached(host, "host_compile", "ccache", K_STATE, environ={})
    assert command == ["ccache", *host]
    assert env["CCACHE_DIR"] == str(K_STATE.parent / "ccache") and env["CCACHE_COMPILERCHECK"] == "content"


@pytest.mark.small
@pytest.mark.parametrize("kind", ["device_compile", "host_link", "device_link"])
def test_only_a_host_compile_runs_through_the_compiler_cache(kind):
    """Checks a device object never comes from the cache, where a stale one loses its kernels."""
    host = ["clang++", "-c", "a.cpp"]
    assert build_gate.cached(host, kind, "ccache", K_STATE, environ={}) == (host, None)


@pytest.mark.small
def test_no_cache_leaves_the_command_alone():
    host = ["clang++", "-c", "a.cpp"]
    assert build_gate.cached(host, "host_compile", "", K_STATE, environ={}) == (host, None)


@pytest.mark.small
def test_a_cache_option_reaches_the_gated_command():
    parsed = build_gate.parse_command_line(
        ["gate", "s", "--cache", "ccache", "--", "clang++", "-c", "a.cpp"])
    assert parsed == (Path("s"), ["clang++", "-c", "a.cpp"], "ccache")


@pytest.mark.small
def test_a_command_line_without_a_command_is_refused_with_the_usage(capsys):
    assert build_gate.main(["gate", "s", "--cache"]) == 2
    assert "usage: build_gate.py" in capsys.readouterr().err


@pytest.mark.small
@pytest.mark.parametrize(("kind", "key", "requested", "expected"), [
    ("device_compile", "d:/src/a.cpp", {"d:/src/a.cpp", "b.cpp"}, True),
    ("host_compile", "b.cpp -O0", {"d:/src/a.cpp", "b.cpp"}, True),
    ("host_compile", "c.cpp -O0", {"d:/src/a.cpp", "b.cpp"}, False),
    ("host_link", "b.cpp", {"d:/src/a.cpp", "b.cpp"}, False),
    ("host_compile", "b.cpp", set(), False),
])
def test_only_a_compile_of_a_requested_unit_is_traced(kind, key, requested, expected):
    assert build_gate.wants_time_trace(kind, key, requested) is expected


class _CallRecorder:
    """Records the commands handed to ``subprocess.call`` and answers 0."""

    def __init__(self) -> None:
        self.commands: list[list[str]] = []

    def __call__(self, command, env=None) -> int:
        """Record *command* and report success."""
        self.commands.append(command)
        return 0


@pytest.mark.medium
def test_a_requested_compile_runs_with_the_time_trace_flag_and_skips_the_cache(tmp_path, monkeypatch):
    calls = _CallRecorder()
    monkeypatch.setattr(subprocess, "call", calls)
    build_gate.run(tmp_path / "gate", ["clang++", "-O0", "-c", "a.cpp"], cache="ccache",
                   requested={"a.cpp"})
    assert calls.commands == [["clang++", "-O0", "-c", "a.cpp", "-ftime-trace"]]


@pytest.mark.medium
def test_a_compile_not_requested_runs_through_the_cache_without_the_time_trace_flag(tmp_path, monkeypatch):
    calls = _CallRecorder()
    monkeypatch.setattr(subprocess, "call", calls)
    build_gate.run(tmp_path / "gate", ["clang++", "-O0", "-c", "b.cpp"], cache="ccache",
                   requested={"a.cpp"})
    assert calls.commands == [["ccache", "clang++", "-O0", "-c", "b.cpp"]]


@pytest.mark.small
@pytest.mark.parametrize("name", [
    b"??$parallel_for@V<lambda_1>@@@handler@_V1@sycl@@QEAAXV?$range@$00@12@@Z",
    b"??$single_task@VKernel@@V<lambda_2>@@@handler@_V1@sycl@@QEAAXV<lambda_2>@@@Z",
    b"_ZN4sycl3_V17handler12parallel_forI6KernelLi1EZ4stepvEUlNS0_4itemILi1ELb1EEEE_EEvNS0_5rangeIXT0_EEET1_",
])
def test_a_host_object_that_instantiates_a_kernel_submission_is_found(name):
    assert build_gate.kernel_submission_of(b"\x00junk\x00" + name + b"\x00tail")


@pytest.mark.small
def test_a_host_object_without_one_passes():
    data = b"\x00?submit_impl@queue@_V1@sycl@@\x00?host_task@handler@_V1@sycl@@\x00"
    assert build_gate.kernel_submission_of(data) == ""


@pytest.mark.medium
def test_a_missing_object_passes(tmp_path):
    assert build_gate.kernel_submission_in(tmp_path / "missing.obj") == ""


K_ITANIUM_SINGLE_TASK = b"_ZN4sycl3_V17handler11single_taskI6KernelZ4stepvEUlvE_EEvT0_"

K_COFF_SUBMISSION = b"??$single_task@VKernel@@V<lambda_2>@@@handler@_V1@sycl@@QEAAXV<lambda_2>@@@Z"


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


@pytest.mark.small
def test_an_elf_object_that_defines_a_kernel_submission_is_found():
    data = _elf_object(K_ITANIUM_SINGLE_TASK, shndx=2)
    assert build_gate.defined_symbols(data) == [K_ITANIUM_SINGLE_TASK]


@pytest.mark.small
def test_an_elf_object_whose_debug_information_names_a_submission_passes():
    data = _elf_object(b"_Z4stepv", shndx=2, debug=K_ITANIUM_SINGLE_TASK + b"\x00")
    assert build_gate.defined_symbols(data) == [b"_Z4stepv"]


@pytest.mark.small
def test_an_elf_object_that_only_references_a_submission_passes():
    data = _elf_object(K_ITANIUM_SINGLE_TASK, shndx=0)
    assert build_gate.defined_symbols(data) == []


@pytest.mark.small
def test_a_coff_object_that_defines_a_submission_is_found():
    data = _coff_object(K_COFF_SUBMISSION, section=1)
    assert build_gate.defined_symbols(data) == [K_COFF_SUBMISSION]


@pytest.mark.small
def test_a_coff_object_that_only_references_a_submission_passes():
    data = _coff_object(K_COFF_SUBMISSION, section=0)
    assert build_gate.defined_symbols(data) == []


@pytest.mark.medium
def test_a_host_compile_that_instantiates_a_kernel_fails_and_loses_its_object(tmp_path):
    state = tmp_path / "gate"
    obj = tmp_path / "a.obj"
    writer = (f"open(r'{obj}', 'wb').write(b'??$parallel_for@V<l>@@@handler@_V1@sycl@@Q')")
    code = build_gate.main(["gate", str(state), "--", sys.executable, "-c", writer,
                            "-o", str(obj), "-c", "a.cpp"])
    assert code == 1 and not obj.exists()
