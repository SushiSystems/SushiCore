# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for where ConfigureStep's results are written."""

from __future__ import annotations

from sushicore.provision.sinks import ModuleSink, WorkspaceSink
from sushicore.workspace import read_toml, workspace_file, write_module


def test_module_sink_writes_config_local(tmp_path):
    """Check that module sink writes config local."""
    sink = ModuleSink(tmp_path, ["# test"])
    sink.write_paths("windows", {"cmake_exe": "C:/cmake.exe"})
    doc = read_toml(tmp_path / "config.local.toml")
    assert doc["tool"]["windows"]["cmake_exe"] == "C:/cmake.exe"


def test_workspace_sink_keeps_modules(tmp_path):
    """Check that workspace sink keeps modules."""
    write_module(tmp_path, "sushidsp", tmp_path)
    WorkspaceSink(tmp_path).write_paths("linux", {"ninja_exe": "/usr/bin/ninja"})
    doc = read_toml(workspace_file(tmp_path))
    assert doc["modules"]["sushidsp"] == str(tmp_path).replace("\\", "/")
    assert doc["tool"]["linux"]["ninja_exe"] == "/usr/bin/ninja"


def test_write_tool_sets_a_top_level_key(tmp_path):
    """Check that write tool sets a top level key."""
    sink = ModuleSink(tmp_path, ["# test"])
    sink.write_tool({"toolchain": "intel-llvm"})
    assert read_toml(sink.target)["tool"]["toolchain"] == "intel-llvm"


def test_clear_removes_only_the_tool_table(tmp_path):
    """Check that clear removes only the tool table."""
    write_module(tmp_path, "a", tmp_path)
    sink = WorkspaceSink(tmp_path)
    sink.write_paths("linux", {"ninja_exe": "n"})
    sink.clear()
    doc = read_toml(workspace_file(tmp_path))
    assert not doc.get("tool") and "a" in doc["modules"]


def test_backup_copies_the_existing_file_before_it_changes(tmp_path):
    """Check that backup copies the existing file before it changes."""
    sink = ModuleSink(tmp_path, ["# test"])
    sink.write_paths("linux", {"ninja_exe": "old"})
    before = sink.target.read_bytes()
    backup = sink.backup()
    sink.write_paths("linux", {"ninja_exe": "new"})
    assert backup == sink.target.with_suffix(".toml.bak")
    assert backup.read_bytes() == before


def test_backup_returns_none_when_the_target_is_absent(tmp_path):
    """Check that backup returns none when the target is absent."""
    sink = ModuleSink(tmp_path, ["# test"])
    assert sink.backup() is None
    assert not sink.target.with_suffix(".toml.bak").is_file()
