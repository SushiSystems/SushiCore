# test_lock_file.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the lock file: its text, its reading and its comparison with the files."""

from __future__ import annotations

import pytest

from sushicore.shared_tools import NoLockError, SharedToolsLock, read_lock
from sushicore.shared_tools.lock_file import digest

pytestmark = pytest.mark.medium


def test_a_written_lock_reads_back_the_same(tmp_path):
    """Tag, commit and every path with its hash survive a write and a read."""
    lock = SharedToolsLock("v1.0.0", "a" * 40, {"tools/a.py": digest(b"a"), ".github/SECURITY.md": digest(b"b")})
    lock.write(tmp_path)
    assert read_lock(tmp_path) == lock


def test_differing_names_a_changed_and_a_missing_file(tmp_path):
    """A file with other bytes and a file that is gone are both named, in path order."""
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / "a.py").write_bytes(b"a!")
    (tmp_path / "tools" / "ok.py").write_bytes(b"ok")
    files = {"tools/a.py": digest(b"a"), "tools/gone.py": digest(b"g"), "tools/ok.py": digest(b"ok")}
    assert SharedToolsLock("v1", "c", files).differing(tmp_path) == ["tools/a.py", "tools/gone.py"]


def test_reading_a_repository_without_a_lock_raises(tmp_path):
    """A missing lock is its own error."""
    with pytest.raises(NoLockError):
        read_lock(tmp_path)
