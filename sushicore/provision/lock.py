# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""A cross-process file lock guarding concurrent provisioning."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

if sys.platform == "win32":
    import msvcrt
else:
    import fcntl

_POLL_INTERVAL = 0.1
_UNKNOWN_HOLDER = "unknown"

#: Byte offset `msvcrt.locking` locks, separate from the PID text at offset 0.
_LOCK_BYTE = 1 << 20


class LockTimeout(Exception):
    """Raised when a lock is not acquired before its timeout elapses."""


def _try_lock(fd: int) -> bool:
    """Attempt a non-blocking exclusive OS lock on *fd*; return whether it succeeded."""
    try:
        if sys.platform == "win32":
            os.lseek(fd, _LOCK_BYTE, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        else:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        return False
    return True


def _unlock(fd: int) -> None:
    """Release the OS lock previously acquired on *fd* with :func:`_try_lock`."""
    if sys.platform == "win32":
        os.lseek(fd, _LOCK_BYTE, os.SEEK_SET)
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
    else:
        fcntl.flock(fd, fcntl.LOCK_UN)


class ProvisionLock:
    """A context manager guarding *path* against concurrent provisioning."""

    def __init__(self, path: Path, timeout: float = 600.0) -> None:
        """Bind the lock to *path*, acquired for at most *timeout* seconds.

        Args:
            path: The lock file to open and lock.
            timeout: Seconds to keep retrying before raising :class:`LockTimeout`.
        """
        self._path = path
        self._timeout = timeout
        self._fd: int | None = None

    def __enter__(self) -> "ProvisionLock":
        """Acquire the OS lock on the lock file, polling until *timeout* elapses.

        Raises:
            LockTimeout: The lock is still held by another process at timeout.
        """
        deadline = time.monotonic() + self._timeout
        fd = os.open(self._path, os.O_CREAT | os.O_RDWR)
        while not _try_lock(fd):
            if time.monotonic() >= deadline:
                holder = self._read_holder(fd)
                os.close(fd)
                raise LockTimeout(f"{self._path}: still held by process {holder}")
            time.sleep(_POLL_INTERVAL)
        os.ftruncate(fd, 0)
        os.lseek(fd, 0, os.SEEK_SET)
        os.write(fd, str(os.getpid()).encode("utf-8"))
        self._fd = fd
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Release the OS lock and close the lock file, without deleting it."""
        if self._fd is not None:
            _unlock(self._fd)
            os.close(self._fd)
            self._fd = None

    def _read_holder(self, fd: int) -> str:
        """Return the PID recorded in the lock file, or a placeholder when unreadable."""
        try:
            os.lseek(fd, 0, os.SEEK_SET)
            data = os.read(fd, 64).decode("utf-8").strip()
        except (OSError, UnicodeDecodeError):
            return _UNKNOWN_HOLDER
        return data if data else _UNKNOWN_HOLDER
