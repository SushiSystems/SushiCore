# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the workspace [modules] table."""

from __future__ import annotations

from sushicore.workspace import (
    read_toml, registered_modules, remove_module, workspace_file, write_module)


def test_no_file_means_no_modules(tmp_path):
    assert registered_modules(tmp_path) == {}


def test_write_then_read(tmp_path):
    write_module(tmp_path, "sushidsp", tmp_path / "dsp")
    # write_toml_document normalizes backslashes to forward slashes on write
    # (see sushicore.config_base._emit_table), same as hub's own test_link.py.
    assert registered_modules(tmp_path) == {"sushidsp": str(tmp_path / "dsp").replace("\\", "/")}


def test_write_keeps_the_tool_table(tmp_path):
    target = workspace_file(tmp_path)
    target.parent.mkdir(parents=True)
    target.write_text('[tool.windows]\ncmake_exe = "C:/cmake.exe"\n', encoding="utf-8")
    write_module(tmp_path, "sushidsp", tmp_path / "dsp")
    doc = read_toml(target)
    assert doc["tool"]["windows"]["cmake_exe"] == "C:/cmake.exe"
    assert doc["workspace"]["version"] == "1"


def test_remove_reports_whether_it_removed(tmp_path):
    write_module(tmp_path, "a", tmp_path)
    assert remove_module(tmp_path, "a") is True
    assert remove_module(tmp_path, "a") is False
    assert registered_modules(tmp_path) == {}
