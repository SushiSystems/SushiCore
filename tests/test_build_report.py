# test_build_report.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""A build report reads its edges from the run's .ninja_log records and the gate's peaks."""

from __future__ import annotations

import pytest

from sushicore.build_report import (BuildReport, Edge, EdgeKind, KindTotals, classify,
                                    ninja_log_offset, read_edges, read_report, summarise)
from sushicore.unit_peaks import UnitPeaks


def _peaks(*entries: tuple[str, str, int]) -> UnitPeaks:
    """Return a table in which each (kind, key, peak) was measured exactly."""
    table = UnitPeaks()
    for kind, key, peak in entries:
        table.record(kind, key, peak, exact=True)
    return table


@pytest.mark.medium
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


@pytest.mark.small
def test_a_summary_totals_each_kind_and_lists_the_heaviest_units():
    edges = [Edge("a.obj", EdgeKind.device_compile, 5.0, 0.0),
             Edge("t.exe", EdgeKind.device_link, 2.0, 0.1)]
    report = summarise(edges, _peaks(("device_compile", "a.cpp", 4000)), 2500)
    assert report.kinds["device_compile"].total_seconds == 5.0
    assert report.kinds["device_compile"].peak_mb == 4000
    assert report.heaviest == [(4000, "a.cpp")] and report.lowest_free_mb == 2500


@pytest.mark.medium
def test_a_report_reads_back_as_it_was_written(tmp_path):
    edges = [Edge("a.obj", EdgeKind.device_compile, 5.0, 0.0)]
    report = summarise(edges, _peaks(("device_compile", "a.cpp", 4000)), 2500)
    report.write(tmp_path)
    assert read_report(tmp_path).heaviest == [(4000, "a.cpp")]


@pytest.mark.small
@pytest.mark.parametrize(("output", "expected"), [
    ("bin/tool.exe", EdgeKind.host_link),
    ("CMakeFiles/stamp", EdgeKind.other),
])
def test_link_outputs_and_stamps_are_told_apart(output, expected):
    assert classify(output, set(), set()) is expected


@pytest.mark.small
def test_a_kinds_peak_is_the_largest_of_its_units():
    report = summarise([], _peaks(("device_compile", "a.cpp", 400), ("device_compile", "b.cpp", 900)))
    assert report.kinds["device_compile"].peak_mb == 900


@pytest.mark.medium
def test_ninja_log_offset_is_the_size_of_the_log(tmp_path):
    tmp_path.joinpath(".ninja_log").write_bytes(b"# ninja log v7\n")
    assert ninja_log_offset(tmp_path) == 15


@pytest.mark.small
def test_report_lines_list_kinds_by_total_time_then_the_slowest_and_heaviest_edges():
    report = BuildReport(
        kinds={"host_compile": KindTotals(count=3, total_seconds=30.0, longest_seconds=20.0, peak_mb=900),
               "device_compile": KindTotals(count=2, total_seconds=100.0, longest_seconds=70.0,
                                            peak_mb=4000)},
        wall_seconds=50.0, lowest_free_mb=2500,
        slowest=[(70.0, "a.obj"), (20.0, "b.obj")], heaviest=[(4000, "a.cpp")])
    assert report.lines() == [
        "wall time 50 s, edge time 130 s, 2.6 edges at once on average",
        "device_compile      2 edges       100 s total      70 s longest    4000 MB peak",
        "host_compile        3 edges        30 s total      20 s longest     900 MB peak",
        "lowest free memory 2500 MB",
        "   70.0 s  a.obj",
        "   20.0 s  b.obj",
        "   4000 MB a.cpp",
    ]
