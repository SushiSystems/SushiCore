# test_files_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What the in-memory files promise: the contract of the Files port, with no disk."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.files_memory import MemoryFiles

pytestmark = pytest.mark.small

K_ROOT = Path("repo")


def test_a_written_file_reads_back_and_its_folders_exist():
    files = MemoryFiles()
    files.write_text(K_ROOT / "docs" / "a.md", "text\n")
    assert files.read_text(K_ROOT / "docs" / "a.md") == "text\n"
    assert files.is_dir(K_ROOT / "docs") and files.exists(K_ROOT)
    assert not files.is_file(K_ROOT / "docs")


def test_a_missing_file_is_absent_and_reading_it_raises():
    files = MemoryFiles()
    assert not files.exists(K_ROOT / "a.md")
    with pytest.raises(FileNotFoundError):
        files.read_text(K_ROOT / "a.md")


def test_children_lists_files_and_folders_one_level_down_sorted():
    files = MemoryFiles({K_ROOT / "b.md": "", K_ROOT / "a" / "x" / "y.md": "", K_ROOT / "a" / "z.md": ""})
    assert files.children(K_ROOT) == [K_ROOT / "a", K_ROOT / "b.md"]
    assert files.children(K_ROOT / "none") == []


def test_a_byte_order_mark_is_dropped_on_read():
    files = MemoryFiles({K_ROOT / "a.md": "\ufeffbody"})
    assert files.read_text(K_ROOT / "a.md") == "body"
