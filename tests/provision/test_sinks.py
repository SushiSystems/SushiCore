# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for where ConfigureStep's results are written."""

from __future__ import annotations

from sushicore.provision.sinks import ModuleSink, WorkspaceSink
from sushicore.workspace import read_toml, workspace_file, write_module


def test_module_sink_writes_config_local(tmp_path):
    sink = ModuleSink(tmp_path, ["# test"])
    sink.write_paths("windows", {"cmake_exe": "C:/cmake.exe"})
    doc = read_toml(tmp_path / "config.local.toml")
    assert doc["tool"]["windows"]["cmake_exe"] == "C:/cmake.exe"


def test_workspace_sink_keeps_modules(tmp_path):
    write_module(tmp_path, "sushidsp", tmp_path)
    WorkspaceSink(tmp_path).write_paths("linux", {"ninja_exe": "/usr/bin/ninja"})
    doc = read_toml(workspace_file(tmp_path))
    assert doc["modules"]["sushidsp"] == str(tmp_path).replace("\\", "/")
    assert doc["tool"]["linux"]["ninja_exe"] == "/usr/bin/ninja"


def test_write_tool_sets_a_top_level_key(tmp_path):
    sink = ModuleSink(tmp_path, ["# test"])
    sink.write_tool({"toolchain": "intel-llvm"})
    assert read_toml(sink.target)["tool"]["toolchain"] == "intel-llvm"


def test_clear_removes_only_the_tool_table(tmp_path):
    write_module(tmp_path, "a", tmp_path)
    sink = WorkspaceSink(tmp_path)
    sink.write_paths("linux", {"ninja_exe": "n"})
    sink.clear()
    doc = read_toml(workspace_file(tmp_path))
    assert "tool" not in doc and "a" in doc["modules"]
