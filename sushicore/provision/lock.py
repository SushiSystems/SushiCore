# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""A cross-process file lock guarding concurrent provisioning."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

_POLL_INTERVAL = 0.1


class LockTimeout(Exception):
    """Raised when a lock is not acquired before its timeout elapses."""


def _pid_alive(pid: int) -> bool:
    """Return whether a process with *pid* is currently running.

    Args:
        pid: The process id read from a lock file.
    """
    if sys.platform == "win32":
        import ctypes

        handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


class ProvisionLock:
    """A context manager guarding *path* against concurrent provisioning.

    Acquiring the lock creates *path* exclusively, holding the acquiring
    process's PID; a stale lock file, whose PID is no longer running, is
    removed and retried.
    """

    def __init__(self, path: Path, timeout: float = 600.0) -> None:
        """Bind the lock to *path*, acquired for at most *timeout* seconds.

        Args:
            path: The lock file to create and delete.
            timeout: Seconds to keep retrying before raising :class:`LockTimeout`.
        """
        self._path = path
        self._timeout = timeout

    def __enter__(self) -> "ProvisionLock":
        """Acquire the lock, polling until *timeout* elapses.

        Raises:
            LockTimeout: The lock is still held by a live process at timeout.
        """
        deadline = time.monotonic() + self._timeout
        while True:
            try:
                fd = os.open(self._path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                holder = self._read_holder()
                if holder is not None and not _pid_alive(holder):
                    self._remove_stale()
                    continue
                if time.monotonic() >= deadline:
                    raise LockTimeout(
                        f"{self._path}: still held by process {holder}")
                time.sleep(_POLL_INTERVAL)
                continue
            with os.fdopen(fd, "w") as fh:
                fh.write(str(os.getpid()))
            return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Release the lock by deleting its file."""
        try:
            self._path.unlink()
        except FileNotFoundError:
            pass

    def _read_holder(self) -> int | None:
        """Return the PID recorded in the lock file, or ``None`` when unreadable."""
        try:
            return int(self._path.read_text(encoding="utf-8").strip())
        except (FileNotFoundError, ValueError):
            return None

    def _remove_stale(self) -> None:
        """Delete a lock file whose recorded holder is no longer running."""
        try:
            self._path.unlink()
        except FileNotFoundError:
            pass
