# test_files.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What the disk files promise: the same contract as the in-memory files, on a real folder."""

from __future__ import annotations

import os

import pytest

from sushicore.files import DiskFiles

pytestmark = pytest.mark.medium


def test_a_written_file_reads_back_with_lf_ends_and_its_folders_made(tmp_path):
    files = DiskFiles()
    path = tmp_path / "docs" / "a.md"
    files.write_text(path, "one\ntwo\n")
    assert path.read_bytes() == b"one\ntwo\n"
    assert files.read_text(path) == "one\ntwo\n"
    assert files.is_dir(tmp_path / "docs") and files.exists(path)


def test_children_lists_one_level_sorted_and_an_absent_folder_has_none(tmp_path):
    (tmp_path / "b.md").write_text("")
    (tmp_path / "a").mkdir()
    files = DiskFiles()
    assert files.children(tmp_path) == [tmp_path / "a", tmp_path / "b.md"]
    assert files.children(tmp_path / "none") == []


def test_a_byte_order_mark_is_dropped_on_read(tmp_path):
    path = tmp_path / "a.md"
    path.write_bytes("\ufeffbody".encode("utf-8"))
    assert DiskFiles().read_text(path) == "body"


def test_a_removed_file_is_gone_and_removing_an_absent_one_is_no_fault(tmp_path):
    path = tmp_path / "a.md"
    path.write_text("")
    files = DiskFiles()
    files.remove(path)
    files.remove(path)
    assert not path.exists()


def test_a_file_reports_its_modification_time_and_a_missing_one_reports_none(tmp_path):
    path = tmp_path / "a.md"
    path.write_text("")
    os.utime(path, (1_000_000, 1_000_000))
    files = DiskFiles()
    assert files.modified_time(path) == 1_000_000
    assert files.modified_time(tmp_path / "none") is None
