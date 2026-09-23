# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The toolchain stamp keeps every field across writers and survives a crash mid-write."""

from __future__ import annotations

import json
import os
from pathlib import Path

from sushicore.provision.toolchains import stamp


def test_missing_stamp_reads_empty(tmp_path):
    assert stamp.read_toolchain_stamp(tmp_path) == {}


def test_written_stamp_round_trips(tmp_path):
    stamp.write_toolchain_stamp(tmp_path, "intel/llvm", "nightly-2026-09-01")
    data = stamp.read_toolchain_stamp(tmp_path)
    assert data["source"] == "intel/llvm"
    assert data["tag"] == "nightly-2026-09-01"


def test_adapter_commit_is_recorded_without_losing_the_tag(tmp_path):
    stamp.write_toolchain_stamp(tmp_path, "intel/llvm", "t")
    stamp.record_toolchain_adapter(tmp_path, "cuda", "abc123")
    assert stamp.toolchain_adapter_commit(tmp_path, "cuda") == "abc123"
    assert stamp.read_toolchain_stamp(tmp_path)["tag"] == "t"


def test_toolchains_dir_follows_the_root(provision_home):
    assert stamp.toolchains_dir() == provision_home.resolve() / "toolchains"


def test_write_toolchain_stamp_keeps_an_existing_adapters_key(tmp_path):
    stamp.record_toolchain_adapter(tmp_path, "fake", "commit1")

    stamp.write_toolchain_stamp(tmp_path, "intel/llvm", "nightly-2")

    data = stamp.read_toolchain_stamp(tmp_path)
    assert data["tag"] == "nightly-2"
    assert data["adapters"]["fake"] == "commit1"


def test_record_toolchain_adapter_keeps_the_existing_source_and_tag(tmp_path):
    stamp.write_toolchain_stamp(tmp_path, "intel/llvm", "nightly-1")

    stamp.record_toolchain_adapter(tmp_path, "fake", "commit1")

    data = stamp.read_toolchain_stamp(tmp_path)
    assert data["source"] == "intel/llvm"
    assert data["tag"] == "nightly-1"
    assert data["adapters"]["fake"] == "commit1"


def test_toolchain_adapter_commit_reads_back_a_recorded_commit(tmp_path):
    stamp.record_toolchain_adapter(tmp_path, "fake", "commit1")

    assert stamp.toolchain_adapter_commit(tmp_path, "fake") == "commit1"
    assert stamp.toolchain_adapter_commit(tmp_path, "other") is None


def test_read_toolchain_stamp_returns_empty_on_invalid_json(tmp_path):
    (tmp_path / stamp.TOOLCHAIN_STAMP).write_text("{not json")

    assert stamp.read_toolchain_stamp(tmp_path) == {}


def test_read_toolchain_stamp_returns_empty_on_invalid_utf8(tmp_path):
    (tmp_path / stamp.TOOLCHAIN_STAMP).write_bytes(b"\xff\xfe\x00")

    assert stamp.read_toolchain_stamp(tmp_path) == {}


def test_read_toolchain_stamp_returns_empty_on_a_non_object_top_level(tmp_path):
    (tmp_path / stamp.TOOLCHAIN_STAMP).write_text(json.dumps(["not", "an", "object"]))

    assert stamp.read_toolchain_stamp(tmp_path) == {}


def test_toolchain_adapter_commit_treats_a_non_dict_adapters_as_absent(tmp_path):
    (tmp_path / stamp.TOOLCHAIN_STAMP).write_text(json.dumps({"adapters": "not-a-dict"}))

    assert stamp.toolchain_adapter_commit(tmp_path, "fake") is None


def test_record_toolchain_adapter_replaces_a_non_dict_adapters(tmp_path):
    (tmp_path / stamp.TOOLCHAIN_STAMP).write_text(json.dumps({"adapters": "not-a-dict"}))

    stamp.record_toolchain_adapter(tmp_path, "fake", "commit1")

    data = stamp.read_toolchain_stamp(tmp_path)
    assert data["adapters"] == {"fake": "commit1"}


def test_write_toolchain_stamp_is_atomic_via_a_temp_file_and_replace(tmp_path, monkeypatch):
    calls: list[tuple[str, str]] = []
    real_replace = os.replace

    def spy(src, dst):
        calls.append((Path(src).name, Path(dst).name))
        return real_replace(src, dst)

    monkeypatch.setattr(os, "replace", spy)

    stamp.write_toolchain_stamp(tmp_path, "intel/llvm", "nightly-1")

    assert calls == [(stamp.TOOLCHAIN_STAMP + ".tmp", stamp.TOOLCHAIN_STAMP)]
    assert not (tmp_path / (stamp.TOOLCHAIN_STAMP + ".tmp")).exists()
    data = json.loads((tmp_path / stamp.TOOLCHAIN_STAMP).read_text())
    assert data["tag"] == "nightly-1"


def test_a_failing_replace_removes_the_temp_file(tmp_path, monkeypatch):
    def failing_replace(src, dst):
        raise OSError("disk full")

    monkeypatch.setattr(os, "replace", failing_replace)

    stamp.write_toolchain_stamp(tmp_path, "intel/llvm", "nightly-1")

    assert not (tmp_path / (stamp.TOOLCHAIN_STAMP + ".tmp")).exists()
    assert not (tmp_path / stamp.TOOLCHAIN_STAMP).exists()
