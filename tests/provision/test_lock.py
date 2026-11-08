# test_lock.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the provisioning file lock."""

from __future__ import annotations

import os

import pytest

from sushicore.provision.lock import LockTimeout, ProvisionLock


def _acquires(path) -> bool:
    """Returns True when the lock at *path* is taken within half a second; LockTimeout otherwise fails the test."""
    with ProvisionLock(path, timeout=0.5):
        return True


@pytest.mark.medium
def test_lock_is_released_on_exit(tmp_path):
    """Check that lock is released on exit."""
    path = tmp_path / ".lock"
    with ProvisionLock(path):
        pass
    assert _acquires(path)


class _ManualTime:
    """A clock that moves only when the lock sleeps, so a wait costs no wall-clock time."""

    def __init__(self) -> None:
        """Start at zero."""
        self.now = 0.0

    def clock(self) -> float:
        """Return the current time."""
        return self.now

    def sleep(self, seconds: float) -> None:
        """Move the time on by *seconds*."""
        self.now += seconds


@pytest.mark.medium
def test_second_holder_times_out_naming_the_pid(tmp_path):
    """Check that second holder times out naming the pid."""
    path = tmp_path / ".lock"
    waiting = _ManualTime()
    with ProvisionLock(path):
        with pytest.raises(LockTimeout, match=str(os.getpid())):
            with ProvisionLock(path, timeout=0.3, clock=waiting.clock, sleep=waiting.sleep):
                pass


@pytest.mark.medium
def test_lock_with_garbage_content_does_not_block(tmp_path):
    """Check that lock with garbage content does not block."""
    path = tmp_path / ".lock"
    path.write_text("garbage not a pid", encoding="utf-8")
    assert _acquires(path)


@pytest.mark.medium
def test_lock_creates_its_parent_directory(tmp_path):
    """Check that lock creates its parent directory."""
    path = tmp_path / "missing" / "root" / ".lock"
    with ProvisionLock(path, timeout=0.5):
        assert path.is_file()


@pytest.mark.medium
def test_a_failing_pid_write_leaves_the_lock_usable(tmp_path):
    """Check that a failed pid write raises and leaves the lock file free to take again."""
    def failing_write(fd, data):
        """Fail as a full disk does."""
        raise OSError("disk full")

    with pytest.raises(OSError, match="disk full"):
        with ProvisionLock(tmp_path / ".lock", timeout=0.5, write=failing_write):
            pass
    assert _acquires(tmp_path / ".lock")


@pytest.mark.medium
def test_an_interrupt_while_polling_leaves_the_lock_usable(tmp_path):
    """Check that an interrupt while waiting propagates and the lock can be taken once freed."""
    path = tmp_path / ".lock"

    def interrupt(_seconds):
        """Interrupt as a user pressing Ctrl+C does."""
        raise KeyboardInterrupt

    with ProvisionLock(path):
        with pytest.raises(KeyboardInterrupt):
            with ProvisionLock(path, timeout=5.0, sleep=interrupt):
                pass
    assert _acquires(path)


@pytest.mark.medium
def test_a_failing_unlock_propagates_and_frees_the_lock(tmp_path):
    """Check that a failed unlock raises and the file is free to take afterwards."""
    def failing_unlock(fd):
        """Fail as an unlock of a broken descriptor does."""
        raise OSError("unlock failed")

    held = ProvisionLock(tmp_path / ".lock", timeout=0.5, unlock=failing_unlock)
    held.__enter__()
    with pytest.raises(OSError, match="unlock failed"):
        held.__exit__(None, None, None)
    assert _acquires(tmp_path / ".lock")
