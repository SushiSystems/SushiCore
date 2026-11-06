# test_build_trace.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Time traces beside objects are summed into header, template and per-unit costs."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sushicore import build_trace


def _event(name: str, seconds: float, detail: str = "") -> dict:
    event = {"ph": "X", "name": name, "dur": int(seconds * 1e6)}
    if detail:
        event["args"] = {"detail": detail}
    return event


def _unit(build_dir: Path, name: str, events: list[dict], suffix: str = ".obj") -> None:
    (build_dir / f"{name}{suffix}").write_bytes(b"")
    (build_dir / f"{name}.json").write_text(json.dumps({"traceEvents": events}), encoding="utf-8")


@pytest.mark.small
def test_headers_are_summed_across_units_and_count_each_unit_once():
    summary = build_trace.summarise_events({
        "a.obj": [_event("Source", 2.0, "x/big.hpp"), _event("Source", 1.0, "x\\big.hpp")],
        "b.obj": [_event("Source", 4.0, "x/big.hpp"), _event("Source", 0.5, "x/small.hpp")],
    }, 5)
    assert summary.headers["x/big.hpp"].seconds == pytest.approx(7.0)
    assert summary.headers["x/big.hpp"].units == 2
    assert summary.headers["x/small.hpp"].units == 1


@pytest.mark.small
def test_templates_and_unit_times_are_read():
    summary = build_trace.summarise_events({
        "a.obj": [_event("InstantiateClass", 1.5, "Foo<int>"),
                  _event("InstantiateFunction", 0.5, "bar<int>"),
                  _event("Total Frontend", 3.0), _event("Total Backend", 1.0)],
    }, 5)
    assert summary.templates["Foo<int>"].seconds == pytest.approx(1.5)
    assert summary.units["a.obj"].frontend == pytest.approx(3.0)
    assert summary.units["a.obj"].backend == pytest.approx(1.0)


@pytest.mark.medium
def test_a_json_file_without_an_object_beside_it_is_ignored(tmp_path):
    (tmp_path / "compile_commands.json").write_text("[]", encoding="utf-8")
    (tmp_path / "orphan.json").write_text(json.dumps({"traceEvents": [_event("Total Frontend", 9)]}))
    _unit(tmp_path, "unit", [_event("Total Frontend", 1.0)], suffix=".o")
    assert list(build_trace.summarise_time_traces(tmp_path, 5).units) == ["unit.o"]


@pytest.mark.medium
def test_a_broken_trace_is_skipped(tmp_path):
    (tmp_path / "a.obj").write_bytes(b"")
    (tmp_path / "a.json").write_text("{not json", encoding="utf-8")
    assert build_trace.summarise_time_traces(tmp_path, 5).units == {}


@pytest.mark.small
def test_lines_rank_headers_and_templates_and_list_units_slowest_first():
    lines = build_trace.summarise_events({
        "fast.obj": [_event("Source", 1.0, "small.hpp"), _event("Total Frontend", 1.0)],
        "slow.obj": [_event("Source", 9.0, "big.hpp"), _event("Total Frontend", 8.0),
                     _event("Total Backend", 2.0)],
    }, 1).lines()
    assert "big.hpp" in lines[1] and "small.hpp" not in "\n".join(lines)
    assert lines[-2].endswith("slow.obj") and lines[-1].endswith("fast.obj")


@pytest.mark.small
def test_no_traces_gives_one_line():
    assert build_trace.summarise_events({}, 3).lines() == ["no time traces found"]
