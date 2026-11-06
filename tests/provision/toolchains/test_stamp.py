# test_stamp.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The toolchain stamp keeps every field across writers and survives a crash mid-write."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from sushicore.provision.toolchains import stamp


pytestmark = pytest.mark.medium


def _root_with_stamp(tmp_path: Path, content: bytes | None) -> Path:
    """Return a bundle root whose stamp file holds *content*, or has no stamp when it is None."""
    if content is not None:
        (tmp_path / stamp.TOOLCHAIN_STAMP).write_bytes(content)
    return tmp_path


@pytest.mark.parametrize("content", [
    None,
    b"{not json",
    b"\xff\xfe\x00",
    json.dumps(["not", "an", "object"]).encode("utf-8"),
], ids=["absent", "not-json", "not-utf8", "not-an-object"])
def test_read_toolchain_stamp_returns_empty_for_an_unusable_stamp(tmp_path, content):
    """Check that an absent, undecodable, non-JSON or non-object stamp reads as an empty dict."""
    assert stamp.read_toolchain_stamp(_root_with_stamp(tmp_path, content)) == {}


def test_written_stamp_round_trips(tmp_path):
    """Check that written stamp round trips."""
    stamp.write_toolchain_stamp(tmp_path, "intel/llvm", "nightly-2026-09-01")
    data = stamp.read_toolchain_stamp(tmp_path)
    assert data["source"] == "intel/llvm"
    assert data["tag"] == "nightly-2026-09-01"


@pytest.mark.parametrize(("vendor", "commit", "tag"), [
    ("cuda", "abc123", "t"),
    ("fake", "commit1", "nightly-1"),
])
def test_record_toolchain_adapter_records_the_commit_and_keeps_source_and_tag(
        tmp_path, vendor, commit, tag):
    """Check that recording an adapter commit keeps the stamp's source and tag."""
    stamp.write_toolchain_stamp(tmp_path, "intel/llvm", tag)

    stamp.record_toolchain_adapter(tmp_path, vendor, commit)

    data = stamp.read_toolchain_stamp(tmp_path)
    assert stamp.toolchain_adapter_commit(tmp_path, vendor) == commit
    assert data["source"] == "intel/llvm"
    assert data["tag"] == tag


def test_write_toolchain_stamp_keeps_an_existing_adapters_key(tmp_path):
    """Check that write toolchain stamp keeps an existing adapters key."""
    stamp.record_toolchain_adapter(tmp_path, "fake", "commit1")

    stamp.write_toolchain_stamp(tmp_path, "intel/llvm", "nightly-2")

    data = stamp.read_toolchain_stamp(tmp_path)
    assert data["tag"] == "nightly-2"
    assert data["adapters"]["fake"] == "commit1"


def test_toolchain_adapter_commit_reads_back_a_recorded_commit(tmp_path):
    """Check that toolchain adapter commit reads back a recorded commit."""
    stamp.record_toolchain_adapter(tmp_path, "fake", "commit1")

    assert stamp.toolchain_adapter_commit(tmp_path, "fake") == "commit1"
    assert stamp.toolchain_adapter_commit(tmp_path, "other") is None


def test_toolchain_adapter_commit_treats_a_non_dict_adapters_as_absent(tmp_path):
    """Check that toolchain adapter commit treats a non dict adapters as absent."""
    (tmp_path / stamp.TOOLCHAIN_STAMP).write_text(json.dumps({"adapters": "not-a-dict"}))

    assert stamp.toolchain_adapter_commit(tmp_path, "fake") is None


def test_record_toolchain_adapter_replaces_a_non_dict_adapters(tmp_path):
    """Check that record toolchain adapter replaces a non dict adapters."""
    (tmp_path / stamp.TOOLCHAIN_STAMP).write_text(json.dumps({"adapters": "not-a-dict"}))

    stamp.record_toolchain_adapter(tmp_path, "fake", "commit1")

    data = stamp.read_toolchain_stamp(tmp_path)
    assert data["adapters"] == {"fake": "commit1"}


def test_a_failing_replace_leaves_the_previous_stamp_readable(tmp_path, monkeypatch):
    """Check that a write that fails at the replace keeps the stamp written before it."""
    stamp.write_toolchain_stamp(tmp_path, "intel/llvm", "nightly-1")

    def failing_replace(src, dst):
        """Fail as a full disk does."""
        raise OSError("disk full")

    monkeypatch.setattr(os, "replace", failing_replace)

    stamp.write_toolchain_stamp(tmp_path, "intel/llvm", "nightly-2")

    assert stamp.read_toolchain_stamp(tmp_path)["tag"] == "nightly-1"


def test_a_failing_replace_removes_the_temp_file(tmp_path, monkeypatch):
    """Check that a failing replace removes the temp file."""
    def failing_replace(src, dst):
        """Check that failing replace."""
        raise OSError("disk full")

    monkeypatch.setattr(os, "replace", failing_replace)

    stamp.write_toolchain_stamp(tmp_path, "intel/llvm", "nightly-1")

    assert not (tmp_path / (stamp.TOOLCHAIN_STAMP + ".tmp")).exists()
    assert not (tmp_path / stamp.TOOLCHAIN_STAMP).exists()


def test_a_stamp_with_non_ascii_text_reads_back_as_utf8(tmp_path):
    """Check that a stamp written as UTF-8 reads back with its non-ASCII text."""
    content = json.dumps({"source": "café"}, ensure_ascii=False).encode("utf-8")
    (tmp_path / stamp.TOOLCHAIN_STAMP).write_bytes(content)

    assert stamp.read_toolchain_stamp(tmp_path) == {"source": "café"}
