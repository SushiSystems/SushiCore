# build_report.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Reports one build: what each kind of edge cost in time, and in memory at its peak.

A CLI's build report reads the edges the build ran from `.ninja_log` and the peaks the memory gate
measured (`build_gate.py`), prints them and writes `build_report.json` into the tree.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path

#: The file a report is written to, inside the tree it measures.
K_REPORT_NAME = "build_report.json"

#: How many of the slowest edges a report lists.
K_SLOWEST = 20


class EdgeKind(str, Enum):
    """The kinds of build edge whose costs differ enough to be scheduled apart."""

    host_compile = "host_compile"
    device_compile = "device_compile"
    host_link = "host_link"
    device_link = "device_link"
    other = "other"


@dataclass(frozen=True, slots=True)
class Edge:
    """One edge a build ran: its first output, its kind, its wall time in seconds and when it
    started, in seconds from the start of the Ninja run."""

    output: str
    kind: EdgeKind
    seconds: float
    started: float = 0.0


@dataclass(slots=True)
class KindTotals:
    """What the edges of one kind cost together."""

    count: int = 0
    total_seconds: float = 0.0
    longest_seconds: float = 0.0
    peak_mb: int = 0


@dataclass(slots=True)
class BuildReport:
    """The costs of one build, per kind of edge, with the run's lowest free memory."""

    kinds: dict[str, KindTotals] = field(default_factory=dict)
    wall_seconds: float = 0.0
    lowest_free_mb: int | None = None
    slowest: list[tuple[float, str]] = field(default_factory=list)
    heaviest: list[tuple[int, str]] = field(default_factory=list)

    def peak_mb(self, kind: EdgeKind) -> int:
        """Returns the measured peak of *kind*, zero when none ran."""
        totals = self.kinds.get(kind.value)
        return totals.peak_mb if totals else 0

    def lines(self) -> list[str]:
        """Returns the report as console lines, one kind each, then the slowest edges."""
        busy = sum(t.total_seconds for t in self.kinds.values())
        out = [f"wall time {self.wall_seconds:.0f} s, edge time {busy:.0f} s, "
               f"{busy / self.wall_seconds if self.wall_seconds else 0:.1f} edges at once on average"]
        for name, t in sorted(self.kinds.items(), key=lambda item: -item[1].total_seconds):
            out.append(f"{name:15s} {t.count:5d} edges  {t.total_seconds:8.0f} s total  "
                       f"{t.longest_seconds:6.0f} s longest  {t.peak_mb:6d} MB peak")
        if self.lowest_free_mb is not None:
            out.append(f"lowest free memory {self.lowest_free_mb} MB")
        out += [f"{seconds:7.1f} s  {output}" for seconds, output in self.slowest[:5]]
        out += [f"{peak:7d} MB {source}" for peak, source in self.heaviest[:5]]
        return out

    def write(self, build_dir: Path) -> Path:
        """Writes the report into *build_dir* and returns its path."""
        path = build_dir / K_REPORT_NAME
        path.write_text(json.dumps({"kinds": {k: asdict(v) for k, v in self.kinds.items()},
                                    "wall_seconds": self.wall_seconds,
                                    "lowest_free_mb": self.lowest_free_mb,
                                    "slowest": self.slowest, "heaviest": self.heaviest},
                                   indent=2), encoding="utf-8")
        return path


def read_report(build_dir: Path) -> BuildReport | None:
    """Returns the report last written into *build_dir*, or None when there is none."""
    path = build_dir / K_REPORT_NAME
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return BuildReport(kinds={k: KindTotals(**v) for k, v in data["kinds"].items()},
                       wall_seconds=data.get("wall_seconds", 0.0),
                       lowest_free_mb=data.get("lowest_free_mb"),
                       slowest=[tuple(item) for item in data.get("slowest", [])],
                       heaviest=[tuple(item) for item in data.get("heaviest", [])])


def ninja_log_offset(build_dir: Path) -> int:
    """Returns the size of the tree's `.ninja_log`; the edges a build appends start there."""
    log = build_dir / ".ninja_log"
    return log.stat().st_size if log.is_file() else 0


def _device_objects(build_dir: Path) -> set[str]:
    """Returns the objects whose compile runs a device pass, as forward-slash paths."""
    path = build_dir / "compile_commands.json"
    if not path.is_file():
        return set()
    found = set()
    for entry in json.loads(path.read_text(encoding="utf-8")):
        command = entry.get("command", "")
        match = re.search(r" -o (\S+)", command)
        if match and "-fsycl-targets" in command:
            found.add(match.group(1).replace("\\", "/"))
    return found


def _device_links(build_dir: Path) -> set[str]:
    """Returns the link outputs of `build.ninja` whose link flags carry `-fsycl`."""
    path = build_dir / "build.ninja"
    if not path.is_file():
        return set()
    found = set()
    current = None
    with path.open(encoding="utf-8", errors="replace") as lines:
        for line in lines:
            if line.startswith("build "):
                head = line[6:].split(":", 1)[0].split()
                current = head[0].replace("$:", ":") if head else None
            elif current and line.startswith("  LINK_FLAGS") and "-fsycl" in line:
                found.add(current.replace("\\", "/"))
    return found


def classify(output: str, device_objects: set[str], device_links: set[str]) -> EdgeKind:
    """Returns the kind of the edge whose first output is *output*."""
    if output.endswith((".obj", ".o")):
        return EdgeKind.device_compile if output in device_objects else EdgeKind.host_compile
    name = output.rsplit("/", 1)[-1]
    if output.endswith((".exe", ".dll", ".so")) or ("." not in name and "CMakeFiles" not in output):
        return EdgeKind.device_link if output in device_links else EdgeKind.host_link
    return EdgeKind.other


def read_edges(build_dir: Path, offset: int = 0) -> list[Edge]:
    """Returns the edges `.ninja_log` records from byte *offset* on, one per command.

    A command with several outputs is written once per output with the same hash and times; it
    is one edge, named by its first output.
    """
    log = build_dir / ".ninja_log"
    if not log.is_file():
        return []
    with log.open("rb") as stream:
        stream.seek(offset)
        text = stream.read().decode("utf-8", errors="replace")
    device_objects = _device_objects(build_dir)
    device_links = _device_links(build_dir)
    seen: dict[tuple[str, str, str], str] = {}
    for line in text.splitlines():
        parts = line.split("\t")
        if line.startswith("#") or len(parts) < 5:
            continue
        start, end, _, output, command_hash = parts[:5]
        seen.setdefault((start, end, command_hash), output.replace("\\", "/"))
    return [Edge(output, classify(output, device_objects, device_links),
                 (int(end) - int(start)) / 1000.0, int(start) / 1000.0)
            for (start, end, _), output in seen.items()]


def summarise(edges: list[Edge], peaks: dict[str, int], lowest_free_mb: int | None = None
              ) -> BuildReport:
    """Returns the report of a build that ran *edges*, with the gate's measured *peaks*.

    *peaks* maps each unit to its peak and each kind, as `@<kind>`, to the largest of its units.
    """
    report = BuildReport()
    for edge in edges:
        totals = report.kinds.setdefault(edge.kind.value, KindTotals())
        totals.count += 1
        totals.total_seconds += edge.seconds
        totals.longest_seconds = max(totals.longest_seconds, edge.seconds)
    for key, peak in peaks.items():
        if key.startswith("@"):
            report.kinds.setdefault(key[1:], KindTotals()).peak_mb = int(peak)
    report.lowest_free_mb = lowest_free_mb
    report.heaviest = sorted(((int(peak), key) for key, peak in peaks.items()
                              if not key.startswith("@")), reverse=True)[:K_SLOWEST]
    if edges:
        report.wall_seconds = (max(e.started + e.seconds for e in edges)
                               - min(e.started for e in edges))
    report.slowest = sorted(((e.seconds, e.output) for e in edges), reverse=True)[:K_SLOWEST]
    return report


def of_build(build_dir: Path, offset: int, gate_state: Path) -> BuildReport:
    """Returns the report of the build that appended to *build_dir*'s log from *offset* on."""
    peaks = _read_json(gate_state / "unit_peaks.json")
    ledger = _read_json(gate_state / "ledger.json")
    return summarise(read_edges(build_dir, offset), peaks, ledger.get("lowest_free"))


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
