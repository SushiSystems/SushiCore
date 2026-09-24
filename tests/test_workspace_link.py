# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the module-side link pointer."""

from __future__ import annotations

from sushicore.workspace import WORKSPACE_MARKER, clear_link, read_link, read_toml, write_link


def _workspace(tmp_path):
    """Create a directory carrying the workspace marker and return it."""
    ws = tmp_path / "ws"
    (ws / WORKSPACE_MARKER).mkdir(parents=True)
    return ws


def test_write_then_read_returns_the_workspace(tmp_path):
    ws = _workspace(tmp_path)
    cfg = tmp_path / "mod" / "cli"
    cfg.mkdir(parents=True)
    write_link(cfg, ws)
    assert read_link(cfg) == ws.resolve()


def test_write_keeps_other_tables(tmp_path):
    ws = _workspace(tmp_path)
    cfg = tmp_path / "cli"
    cfg.mkdir()
    (cfg / "config.local.toml").write_text('[tool]\ncmake_exe = "C:/cmake.exe"\n')
    write_link(cfg, ws)
    doc = read_toml(cfg / "config.local.toml")
    assert doc["tool"]["cmake_exe"] == "C:/cmake.exe"
    assert "workspace" in doc["link"]


def test_read_ignores_a_pointer_to_a_deleted_workspace(tmp_path):
    ws = _workspace(tmp_path)
    cfg = tmp_path / "cli"
    cfg.mkdir()
    write_link(cfg, ws)
    (ws / WORKSPACE_MARKER).rmdir()
    assert read_link(cfg) is None


def test_clear_removes_the_file_when_nothing_else_remains(tmp_path):
    ws = _workspace(tmp_path)
    cfg = tmp_path / "cli"
    cfg.mkdir()
    write_link(cfg, ws)
    assert clear_link(cfg) is True
    assert not (cfg / "config.local.toml").exists()
    assert clear_link(cfg) is False


def test_clear_keeps_the_file_when_other_tables_remain(tmp_path):
    ws = _workspace(tmp_path)
    cfg = tmp_path / "cli"
    cfg.mkdir()
    (cfg / "config.local.toml").write_text('[tool]\ncmake_exe = "C:/cmake.exe"\n')
    write_link(cfg, ws)
    assert clear_link(cfg) is True
    assert read_toml(cfg / "config.local.toml") == {"tool": {"cmake_exe": "C:/cmake.exe"}}
