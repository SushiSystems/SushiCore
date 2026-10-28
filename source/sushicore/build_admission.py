# build_admission.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Puts a tree's compiles and links behind the memory gate, `build_gate.py`.

The reasoning is in docs/architecture/OVERVIEW.md, section `build_admission`.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import Sequence

from .errors import SushiCoreError

#: The folder beside a checkout's build trees where the gate keeps its ledger and measured peaks.
K_STATE_FOLDER = "build_gate"

#: The file in the state folder that stops every build of the checkout.
K_STOP_FILE = "stop"


#: The file in the state folder that lists the units whose compiles are time-traced.
K_TIME_TRACE_FILE = "time_trace.txt"


class BuildStoppedError(SushiCoreError):
    """Reports a build refused because the gate's stop file exists."""

    def __init__(self, stop: Path) -> None:
        """Name the stop file and how to lift it."""
        super().__init__(f"{stop} exists, so the memory gate admits nothing; delete it to build.")
        self.stop = stop


def state_dir(build_dir: Path) -> Path:
    """Returns the folder the gate of *build_dir*, and of every tree beside it, keeps its state in."""
    return Path(build_dir).parent / K_STATE_FOLDER


def stop_file(build_dir: Path) -> Path:
    """Returns the file whose presence makes the gate of *build_dir* fail every edge."""
    return state_dir(build_dir) / K_STOP_FILE


def refuse_a_stopped_gate(build_dir: Path) -> None:
    """Raises BuildStoppedError while the stop file of *build_dir*'s gate exists."""
    stop = stop_file(build_dir)
    if stop.exists():
        raise BuildStoppedError(stop)


def gate_script() -> Path:
    """Returns the gate script, which runs on its own rather than through the package."""
    return Path(__file__).resolve().parent / "build_gate.py"


def compiler_cache(configured: str = "") -> str:
    """Returns the ccache executable a build caches host compiles with, or "" for none.

    *configured* is the CLI's `ccache_exe` setting; empty looks for `ccache` on PATH.
    """
    if configured:
        return configured if Path(configured).is_file() else ""
    return shutil.which("ccache") or ""


def request_time_traces(build_dir: Path, sources: Sequence[str]) -> Path:
    """Asks the gate of *build_dir* to time-trace the compiles of *sources* and returns the file.

    Keys are written as the gate keys a unit: forward slashes, lower case.
    """
    path = state_dir(build_dir) / K_TIME_TRACE_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    keys = [source.replace("\\", "/").lower() for source in sources]
    path.write_text("".join(f"{key}\n" for key in keys), encoding="utf-8")
    return path


def clear_time_traces(build_dir: Path) -> None:
    """Removes the time-trace request of *build_dir*'s gate, if there is one."""
    (state_dir(build_dir) / K_TIME_TRACE_FILE).unlink(missing_ok=True)


def launcher_defines(build_dir: Path, cache: str = "") -> tuple[str, ...]:
    """Returns the cache entries that run every compile and link of *build_dir* through the gate.

    A non-empty *cache* is the ccache executable the gate runs host compiles through.
    """
    words = [Path(sys.executable).as_posix(), "-I", gate_script().as_posix(),
             state_dir(build_dir).as_posix()]
    if cache:
        words += ["--cache", Path(cache).as_posix()]
    launcher = ";".join([*words, "--"])
    return (f"CMAKE_CXX_COMPILER_LAUNCHER={launcher}", f"CMAKE_CXX_LINKER_LAUNCHER={launcher}")


def hardware_threads() -> int:
    """Returns the job count: CMAKE_BUILD_PARALLEL_LEVEL when it is set, else the threads."""
    stated = os.environ.get("CMAKE_BUILD_PARALLEL_LEVEL", "")
    return int(stated) if stated.isdigit() and int(stated) > 0 else (os.cpu_count() or 1)
