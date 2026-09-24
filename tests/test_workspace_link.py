# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the module-side link pointer."""

from __future__ import annotations

import pytest

from sushicore.workspace import tomllib

from sushicore.workspace import (
    WORKSPACE_MARKER,
    LinkEditError,
    clear_link,
    read_link,
    read_toml,
    write_link,
)


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


def test_read_raises_on_a_malformed_local_config_as_config_loading_does(tmp_path):
    cfg = tmp_path / "cli"
    cfg.mkdir()
    (cfg / "config.local.toml").write_text("[link", encoding="utf-8")
    with pytest.raises(tomllib.TOMLDecodeError):
        read_link(cfg)


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


_USER_TEXT = (
    "# my settings\n"
    "[tool]\n"
    "jobs = 8  # parallel\n"
    'cmake_exe = "C:/cmake.exe"\n'
)


def test_write_and_clear_keep_comments_and_non_string_values(tmp_path):
    ws = _workspace(tmp_path)
    cfg = tmp_path / "cli"
    cfg.mkdir()
    local = cfg / "config.local.toml"
    local.write_text(_USER_TEXT, encoding="utf-8")
    write_link(cfg, ws)
    text = local.read_text(encoding="utf-8")
    assert text.startswith(_USER_TEXT)
    assert read_toml(local)["tool"]["jobs"] == 8
    assert read_link(cfg) == ws.resolve()
    assert clear_link(cfg) is True
    assert local.read_text(encoding="utf-8") == _USER_TEXT


def test_rewriting_the_link_replaces_only_its_table(tmp_path):
    first = _workspace(tmp_path)
    second = tmp_path / "ws2"
    (second / WORKSPACE_MARKER).mkdir(parents=True)
    cfg = tmp_path / "cli"
    cfg.mkdir()
    local = cfg / "config.local.toml"
    local.write_text('[link]\nworkspace = "x"\n\n' + _USER_TEXT, encoding="utf-8")
    write_link(cfg, first)
    write_link(cfg, second)
    assert read_link(cfg) == second.resolve()
    assert local.read_text(encoding="utf-8").endswith(_USER_TEXT)
    assert local.read_text(encoding="utf-8").count("[link]") == 1


def test_a_relative_pointer_resolves_against_the_config_dir(tmp_path):
    ws = _workspace(tmp_path)
    cfg = tmp_path / "mod" / "cli"
    cfg.mkdir(parents=True)
    (cfg / "config.local.toml").write_text('[link]\nworkspace = "../../ws"\n', encoding="utf-8")
    assert read_link(cfg) == ws.resolve()


def _local(tmp_path, text):
    """Create a config dir whose local config holds *text* as bytes and return both."""
    cfg = tmp_path / "cli"
    cfg.mkdir()
    local = cfg / "config.local.toml"
    local.write_bytes(text.encode("utf-8"))
    return cfg, local


@pytest.mark.parametrize("header", ["[link] # mine", "  [ link ]  "])
def test_a_decorated_header_is_replaced_not_duplicated(tmp_path, header):
    ws = _workspace(tmp_path)
    cfg, local = _local(tmp_path, f'{header}\nworkspace = "x"\n\n{_USER_TEXT}')
    write_link(cfg, ws)
    assert read_link(cfg) == ws.resolve()
    assert local.read_text(encoding="utf-8").endswith(_USER_TEXT)
    assert clear_link(cfg) is True
    assert local.read_text(encoding="utf-8") == _USER_TEXT


def test_a_root_inline_table_is_refused_and_left_unchanged(tmp_path):
    ws = _workspace(tmp_path)
    text = 'link = { workspace = "x" }\n' + _USER_TEXT
    cfg, local = _local(tmp_path, text)
    with pytest.raises(LinkEditError):
        write_link(cfg, ws)
    with pytest.raises(LinkEditError):
        clear_link(cfg)
    assert local.read_text(encoding="utf-8") == text


def test_a_header_inside_a_multiline_string_never_corrupts_the_file(tmp_path):
    ws = _workspace(tmp_path)
    text = '[tool]\nnote = """\n[link]\nworkspace = "x"\n"""\n'
    cfg, local = _local(tmp_path, text)
    with pytest.raises(LinkEditError):
        write_link(cfg, ws)
    assert local.read_text(encoding="utf-8") == text
    assert clear_link(cfg) is False
    assert local.read_text(encoding="utf-8") == text


def test_crlf_line_endings_are_preserved(tmp_path):
    ws = _workspace(tmp_path)
    text = _USER_TEXT.replace("\n", "\r\n")
    cfg, local = _local(tmp_path, text)
    write_link(cfg, ws)
    written = local.read_bytes().decode("utf-8")
    assert written.startswith(text)
    assert "\n" not in written.replace("\r\n", "")
    assert clear_link(cfg) is True
    assert local.read_bytes().decode("utf-8") == text
