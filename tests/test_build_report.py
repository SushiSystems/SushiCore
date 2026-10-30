# test_build_report.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""A build report reads its edges from the run's .ninja_log records and the gate's peaks."""

from __future__ import annotations

import pytest

from sushicore.build_report import EdgeKind, classify, read_edges, read_report, summarise

pytestmark = pytest.mark.small


def test_edges_are_read_from_the_offset_once_per_command(tmp_path):
    """Checks a multi-output command is one edge and an earlier run is not counted."""
    old = "# ninja log v7\n0\t1000\t0\told.obj\taaaa\n"
    tmp_path.joinpath(".ninja_log").write_text(
        old + "0\t5000\t0\ta.obj\tbbbb\n0\t5000\t0\ta.pdb\tbbbb\n100\t2100\t0\tt.exe\tcccc\n")
    tmp_path.joinpath("compile_commands.json").write_text(
        '[{"command": "clang++ -fsycl -fsycl-targets=spir64 -o a.obj -c a.cpp", "file": "a.cpp"}]')
    tmp_path.joinpath("build.ninja").write_text(
        "build t.exe: CXX_EXECUTABLE_LINKER a.obj\n  LINK_FLAGS = -fsycl\n")
    edges = read_edges(tmp_path, len(old))
    assert sorted((e.output, e.kind, e.seconds) for e in edges) == [
        ("a.obj", EdgeKind.device_compile, 5.0), ("t.exe", EdgeKind.device_link, 2.0)]
    report = summarise(edges, {"a.cpp": 4000, "@device_compile": 4000}, 2500)
    assert report.kinds["device_compile"].total_seconds == 5.0
    assert report.kinds["device_compile"].peak_mb == 4000
    assert report.heaviest == [(4000, "a.cpp")] and report.lowest_free_mb == 2500
    report.write(tmp_path)
    assert read_report(tmp_path).heaviest == [(4000, "a.cpp")]


def test_link_outputs_and_stamps_are_told_apart():
    assert classify("bin/tool.exe", set(), set()) is EdgeKind.host_link
    assert classify("CMakeFiles/stamp", set(), set()) is EdgeKind.other


def test_the_count_of_a_kinds_units_is_neither_a_unit_nor_a_kind():
    report = summarise([], {"a.cpp": 400, "@device_compile": 400, "#device_compile": 9}, 2500)
    assert report.heaviest == [(400, "a.cpp")]
    assert set(report.kinds) == {"device_compile"}


def test_the_reserved_prefixes_equal_those_of_the_gate():
    from sushicore import build_gate, build_report

    assert (build_report.K_KIND_PREFIX, build_report.K_COUNT_PREFIX) == (
        build_gate.K_KIND_PREFIX, build_gate.K_COUNT_PREFIX)
