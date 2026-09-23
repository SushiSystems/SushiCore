# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the provisioning file lock."""

from __future__ import annotations

import os

import pytest

from sushicore.provision import lock
from sushicore.provision.lock import LockTimeout, ProvisionLock


def test_lock_is_released_on_exit(tmp_path):
    """Check that lock is released on exit."""
    path = tmp_path / ".lock"
    with ProvisionLock(path):
        pass
    with ProvisionLock(path, timeout=0.5):
        pass


def test_second_holder_times_out_naming_the_pid(tmp_path):
    """Check that second holder times out naming the pid."""
    path = tmp_path / ".lock"
    with ProvisionLock(path):
        with pytest.raises(LockTimeout, match=str(os.getpid())):
            with ProvisionLock(path, timeout=0.3):
                pass


def test_lock_with_garbage_content_does_not_block(tmp_path):
    """Check that lock with garbage content does not block."""
    path = tmp_path / ".lock"
    path.write_text("garbage not a pid", encoding="utf-8")
    with ProvisionLock(path, timeout=0.5):
        pass


def test_lock_creates_its_parent_directory(tmp_path):
    """Check that lock creates its parent directory."""
    path = tmp_path / "missing" / "root" / ".lock"
    with ProvisionLock(path, timeout=0.5):
        assert path.is_file()


def _track_closes(monkeypatch):
    """Record every descriptor ``lock`` closes, still closing it."""
    closed = []
    real_close = os.close

    def close(fd):
        """Check that close."""
        closed.append(fd)
        real_close(fd)

    monkeypatch.setattr(lock.os, "close", close)
    return closed


def test_a_failing_pid_write_closes_the_descriptor(tmp_path, monkeypatch):
    """Check that a failing pid write closes the descriptor."""
    closed = _track_closes(monkeypatch)

    def failing_write(fd, data):
        """Check that failing write."""
        raise OSError("disk full")

    monkeypatch.setattr(lock.os, "write", failing_write)
    with pytest.raises(OSError, match="disk full"):
        with ProvisionLock(tmp_path / ".lock", timeout=0.5):
            pass
    assert len(closed) == 1
    monkeypatch.undo()
    with ProvisionLock(tmp_path / ".lock", timeout=0.3):
        pass


def test_an_interrupt_while_polling_closes_the_descriptor(tmp_path, monkeypatch):
    """Check that an interrupt while polling closes the descriptor."""
    path = tmp_path / ".lock"
    with ProvisionLock(path):
        closed = _track_closes(monkeypatch)

        def interrupt(_seconds):
            """Check that interrupt."""
            raise KeyboardInterrupt

        monkeypatch.setattr(lock.time, "sleep", interrupt)
        with pytest.raises(KeyboardInterrupt):
            with ProvisionLock(path, timeout=5.0):
                pass
        assert len(closed) == 1


def test_a_failing_unlock_still_closes_the_descriptor(tmp_path, monkeypatch):
    """Check that a failing unlock still closes the descriptor."""
    held = ProvisionLock(tmp_path / ".lock", timeout=0.5)
    held.__enter__()
    closed = _track_closes(monkeypatch)

    def failing_unlock(fd):
        """Check that failing unlock."""
        raise OSError("unlock failed")

    monkeypatch.setattr(lock, "_unlock", failing_unlock)
    with pytest.raises(OSError, match="unlock failed"):
        held.__exit__(None, None, None)
    assert len(closed) == 1
