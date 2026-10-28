# build_gate.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Admits one compile or link into the build only when the memory it will need is free.

Run as `python -I build_gate.py <state dir> [--cache <ccache>] -- <command>`, the launcher
`build_admission` gives a tree. Edges are admitted in arrival order against their measured peaks;
a `stop` file in the state folder fails every waiting edge. The reasoning is in
docs/architecture/OVERVIEW.md, section `build_gate`.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

#: Memory left to everything else on the machine, in megabytes.
K_RESERVE_MB = 1536

#: Peaks assumed for an edge of a kind no build has measured, in megabytes.
K_DEFAULT_PEAK_MB = {"device_compile": 8400, "host_compile": 1000,
                     "device_link": 3000, "host_link": 1500}

#: The compiler cache's size cap, which ccache reads as CCACHE_MAXSIZE.
K_CACHE_SIZE = "5G"

#: Seconds between two admission checks of a waiting edge.
K_POLL = 0.25

#: Seconds the head of the queue may wait while lighter edges behind it are admitted around it.
K_BACKFILL_WINDOW = 10.0

K_PEAKS = "unit_peaks.json"
K_LEDGER = "ledger.json"
K_LOCK = "gate.lock"

#: While this file exists in the state folder, the gate admits nothing.
K_STOP = "stop"


def edge_of(command: list[str]) -> tuple[str, str]:
    """Returns the kind of the edge *command* runs and the key its peak is kept under."""
    device = any(arg == "-fsycl" or arg.startswith("-fsycl-targets") for arg in command)
    link = "-c" not in command
    if link:
        key = next((arg[5:] for arg in command if arg.lower().startswith(("/out:", "-out:"))), "")
        if not key and "-o" in command:
            key = command[command.index("-o") + 1]
    else:
        key = command[command.index("-c") + 1] if command.index("-c") + 1 < len(command) else ""
    kind = ("device_" if device else "host_") + ("link" if link else "compile")
    # The same unit peaks differently at another optimisation level, so the level is in its key.
    level = next((arg for arg in reversed(command) if arg in ("-O0", "-O1", "-O2", "-O3", "-Os")), "")
    return kind, key.replace("\\", "/").lower() + (f" {level}" if level else "")


def free_memory_mb() -> int:
    """Returns the physical memory free now, in megabytes."""
    if sys.platform == "win32":
        import ctypes

        class MemoryStatus(ctypes.Structure):
            _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong),
                        ("total_phys", ctypes.c_ulonglong), ("avail_phys", ctypes.c_ulonglong),
                        ("total_page", ctypes.c_ulonglong), ("avail_page", ctypes.c_ulonglong),
                        ("total_virtual", ctypes.c_ulonglong), ("avail_virtual", ctypes.c_ulonglong),
                        ("avail_extended", ctypes.c_ulonglong)]

        status = MemoryStatus()
        status.length = ctypes.sizeof(MemoryStatus)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
        return status.avail_phys >> 20
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) >> 10
    return 0


def alive(pid: int) -> bool:
    """Returns whether process *pid* is still running."""
    if sys.platform == "win32":
        import ctypes
        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)  # QUERY_LIMITED_INFORMATION
        if not handle:
            return False
        code = ctypes.c_ulong()
        ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
        ctypes.windll.kernel32.CloseHandle(handle)
        return code.value == 259  # STILL_ACTIVE
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


class Locked:
    """Holds the state directory's lock file for the length of a `with` block."""

    def __init__(self, state: Path) -> None:
        self._path = state / K_LOCK

    def __enter__(self) -> "Locked":
        self._file = open(self._path, "a+b")
        if sys.platform == "win32":
            import msvcrt
            while True:
                try:
                    self._file.seek(0)
                    msvcrt.locking(self._file.fileno(), msvcrt.LK_LOCK, 1)
                    break
                except OSError:
                    continue
        else:
            import fcntl
            fcntl.flock(self._file, fcntl.LOCK_EX)
        return self

    def __exit__(self, *_exc) -> None:
        if sys.platform == "win32":
            import msvcrt
            self._file.seek(0)
            msvcrt.locking(self._file.fileno(), msvcrt.LK_UNLCK, 1)
        self._file.close()


def _read(path: Path, empty: dict) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return empty


def _write(path: Path, data: dict) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data), encoding="utf-8")
    os.replace(temporary, path)


def expected_peak(peaks: dict, kind: str, key: str) -> int:
    """Returns the peak to reserve for the edge *key* of *kind*.

    A unit measured before is reserved at its own peak. A unit not seen yet is reserved at the
    larger of its kind's default and the largest peak its kind has shown: the units measured so
    far may be the light ones, and a guess below the heavy ones runs the machine out of memory.
    """
    if key in peaks:
        return int(peaks[key])
    return max(K_DEFAULT_PEAK_MB[kind], int(peaks.get("@" + kind, 0)))


def admit(ledger: dict, me: int, expected: int, free_mb: int, now: float) -> bool:
    """Admits *me* into *ledger* when its reservation fits and its turn has come.

    Its turn has come when it heads the queue, or when it fits and the head has waited less than
    the backfill window. The budget is set by the first edge to arrive at an idle gate, from the
    memory free then, so it counts what other programs hold at the start of a build and not what
    this build holds later; memory another program frees during the build is used as well. An edge alone is always admitted, whatever its peak: nothing else
    can make room.
    """
    running = ledger.setdefault("running", {})
    queue = ledger.setdefault("queue", [])
    for pid in [pid for pid in running if not alive(int(pid))]:
        del running[pid]
    queue[:] = [entry for entry in queue if alive(entry[0])]
    if not running and not queue:
        ledger["budget"] = max(0, free_mb - K_RESERVE_MB)
        ledger["lowest_free"] = free_mb
    ledger["lowest_free"] = min(free_mb, ledger.get("lowest_free", free_mb))
    if me not in (entry[0] for entry in queue):
        queue.append([me, expected, now])
    reserved = sum(running.values())
    # Free memory already excludes what running edges hold, so their reservations count twice.
    room = max(ledger["budget"], free_mb - K_RESERVE_MB)
    fits = reserved + expected <= room and free_mb >= K_RESERVE_MB
    head = queue[0]
    if head[0] == me:
        if running and not fits:
            return False
    elif not fits or now - head[2] >= K_BACKFILL_WINDOW:
        return False
    queue[:] = [entry for entry in queue if entry[0] != me]
    running[str(me)] = expected
    return True


class PeakMeter:
    """Measures the peak memory of this process and every process it starts, in megabytes."""

    def __init__(self) -> None:
        self._job = None
        if sys.platform == "win32":
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.CreateJobObjectW.restype = ctypes.c_void_p
            self._job = kernel32.CreateJobObjectW(None, None)
            if self._job:
                kernel32.AssignProcessToJobObject(ctypes.c_void_p(self._job),
                                                  ctypes.c_void_p(kernel32.GetCurrentProcess()))

    def peak_mb(self) -> int:
        """Returns the peak so far: committed memory of the job on Windows, resident set on Linux."""
        if sys.platform != "win32":
            import resource
            return resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss >> 10
        if not self._job:
            return 0
        import ctypes
        buffer = (ctypes.c_ulonglong * 18)()  # JOBOBJECT_EXTENDED_LIMIT_INFORMATION, 144 bytes
        ok = ctypes.windll.kernel32.QueryInformationJobObject(
            ctypes.c_void_p(self._job), 9, ctypes.byref(buffer), ctypes.sizeof(buffer), None)
        return int(buffer[17]) >> 20 if ok else 0  # PeakJobMemoryUsed


def cached(command: list[str], kind: str, cache: str, state: Path) -> tuple[list[str], dict | None]:
    """Returns *command* run through the compiler cache *cache*, and the environment it needs.

    Only a host compile is cached. A device compile's object carries device images, and a stale
    one is a kernel missing at run time that no build step reports. The cache sits beside the
    gate's state folder and checks the compiler by its content, not its time stamp.
    """
    if not cache or kind != "host_compile":
        return command, None
    env = dict(os.environ, CCACHE_DIR=str(state.parent / "ccache"), CCACHE_MAXSIZE=K_CACHE_SIZE,
               CCACHE_COMPILERCHECK="content", CCACHE_SLOPPINESS="pch_defines,time_macros")
    return [cache, *command], env


def run(state: Path, command: list[str], cache: str = "") -> int:
    """Runs *command* once the gate admits it, records its peak and returns its exit code."""
    state.mkdir(parents=True, exist_ok=True)
    kind, key = edge_of(command)
    me = os.getpid()
    with Locked(state):
        expected = expected_peak(_read(state / K_PEAKS, {}), kind, key)
    while True:
        if (state / K_STOP).exists():
            print(f"build_gate: {state / K_STOP} exists; not starting {key}", file=sys.stderr)
            with Locked(state):
                ledger = _read(state / K_LEDGER, {})
                ledger.setdefault("queue", [])[:] = [e for e in ledger.get("queue", []) if e[0] != me]
                _write(state / K_LEDGER, ledger)
            return 1
        with Locked(state):
            ledger = _read(state / K_LEDGER, {})
            admitted = admit(ledger, me, expected, free_memory_mb(), time.time())
            _write(state / K_LEDGER, ledger)
        if admitted:
            break
        time.sleep(K_POLL)

    meter = PeakMeter()
    command, env = cached(command, kind, cache, state)
    try:
        code = subprocess.call(command, env=env)
    finally:
        peak = meter.peak_mb()
        with Locked(state):
            ledger = _read(state / K_LEDGER, {})
            ledger.get("running", {}).pop(str(me), None)
            _write(state / K_LEDGER, ledger)
            if peak:
                peaks = _read(state / K_PEAKS, {})
                # The largest seen across build types: a unit's host pass is heavier at -O3.
                peaks[key] = max(peak, int(peaks.get(key, 0)))
                peaks["@" + kind] = max(peak, int(peaks.get("@" + kind, 0)))
                _write(state / K_PEAKS, peaks)
    return code


def main(argv: list[str]) -> int:
    """Runs `build_gate.py <state dir> [--cache <ccache>] -- <command...>`."""
    cache = ""
    rest = argv[2:]
    if rest[:1] == ["--cache"] and len(rest) > 1:
        cache, rest = rest[1], rest[2:]
    if len(argv) < 2 or len(rest) < 2 or rest[0] != "--":
        print("usage: build_gate.py <state dir> [--cache <ccache>] -- <command...>", file=sys.stderr)
        return 2
    return run(Path(argv[1]), rest[1:], cache)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
