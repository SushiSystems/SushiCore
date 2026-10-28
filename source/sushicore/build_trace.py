# build_trace.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Summarises the clang time traces a build left beside its objects.

The reasoning is in docs/architecture/OVERVIEW.md, section `build_trace`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

K_OBJECT_SUFFIXES = (".obj", ".o")


@dataclass(slots=True)
class Cost:
    """The time one header or one template cost, and how many units paid it."""

    seconds: float = 0.0
    units: int = 0


@dataclass(slots=True)
class UnitTimes:
    """The frontend and backend time of one unit, in seconds."""

    frontend: float = 0.0
    backend: float = 0.0


@dataclass(slots=True)
class TraceSummary:
    """What the time traces of a tree say: the costliest headers and templates, and each unit."""

    headers: dict[str, Cost] = field(default_factory=dict)
    templates: dict[str, Cost] = field(default_factory=dict)
    units: dict[str, UnitTimes] = field(default_factory=dict)
    top: int = 20

    def lines(self) -> list[str]:
        """Returns console lines: the top headers, the top templates, then each unit."""
        if not self.units:
            return ["no time traces found"]
        out = [f"headers by total parse time, top {self.top}"]
        out += _ranked(self.headers, self.top)
        out.append(f"template instantiations by total time, top {self.top}")
        out += _ranked(self.templates, self.top)
        out.append("units, slowest first")
        for name, times in sorted(self.units.items(), key=lambda item: -sum(_pair(item[1]))):
            out.append(f"{times.frontend:8.1f} s frontend  {times.backend:8.1f} s backend  {name}")
        return out


def summarise_time_traces(build_dir: Path, top: int) -> TraceSummary:
    """Reads every time trace under *build_dir* that sits beside an object and sums it up.

    Clang writes `<object stem>.json` beside `<object>`. Times are inclusive: a header that
    includes another counts the inner parse in its own total.
    """
    summary = TraceSummary(top=top)
    for suffix in K_OBJECT_SUFFIXES:
        for obj in sorted(build_dir.rglob(f"*{suffix}")):
            trace = obj.with_suffix(".json")
            if trace.is_file():
                _add(summary, obj.relative_to(build_dir).as_posix(), trace)
    return summary


def _add(summary: TraceSummary, unit: str, trace: Path) -> None:
    try:
        events = json.loads(trace.read_text(encoding="utf-8")).get("traceEvents", [])
    except (OSError, ValueError):
        return
    times = summary.units.setdefault(unit, UnitTimes())
    headers: dict[str, float] = {}
    templates: dict[str, float] = {}
    for event in events:
        name, seconds = event.get("name"), event.get("dur", 0) / 1e6
        detail = event.get("args", {}).get("detail", "").replace("\\", "/")
        if name == "Source" and detail:
            headers[detail] = headers.get(detail, 0.0) + seconds
        elif name in ("InstantiateClass", "InstantiateFunction") and detail:
            templates[detail] = templates.get(detail, 0.0) + seconds
        elif name == "Total Frontend":
            times.frontend += seconds
        elif name == "Total Backend":
            times.backend += seconds
    _charge(summary.headers, headers)
    _charge(summary.templates, templates)


def _charge(costs: dict[str, Cost], unit_seconds: dict[str, float]) -> None:
    """Adds one unit's time per name into *costs*; each name counts the unit once."""
    for name, seconds in unit_seconds.items():
        cost = costs.setdefault(name, Cost())
        cost.seconds += seconds
        cost.units += 1


def _pair(times: UnitTimes) -> tuple[float, float]:
    return times.frontend, times.backend


def _ranked(costs: dict[str, Cost], top: int) -> list[str]:
    ranked = sorted(costs.items(), key=lambda item: -item[1].seconds)[:top]
    return [f"{cost.seconds:8.1f} s  {cost.units:4d} units  {name}" for name, cost in ranked]
