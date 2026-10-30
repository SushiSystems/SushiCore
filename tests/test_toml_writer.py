# test_toml_writer.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The TOML writer renders the tables it is given and refuses what it cannot keep."""

import pytest

from sushicore.toml_writer import write_toml_document
from sushicore.workspace import read_toml


pytestmark = pytest.mark.small


def test_it_renders_tool_first_and_the_other_tables_sorted(tmp_path):
    target = tmp_path / "workspace.toml"
    write_toml_document(
        target,
        {"modules": {"sushiai": "D:\Projects\sushiai"}, "tool": {"toolchain": "acpp"},
         "workspace": {"version": "1"}},
        ["# header"])
    body = target.read_text(encoding="utf-8")
    assert body.index("[tool]") < body.index("[modules]") < body.index("[workspace]")
    assert 'sushiai = "D:/Projects/sushiai"' in body


def test_what_it_writes_reads_back_as_the_same_tables(tmp_path):
    target = tmp_path / "a.toml"
    write_toml_document(target, {"tool": {"x": "1", "flag": True}, "modules": {"m": "p"}}, ["# h"])
    assert read_toml(target) == {"tool": {"x": "1", "flag": True}, "modules": {"m": "p"}}


def test_a_value_that_is_not_a_string_in_a_table_raises_instead_of_vanishing(tmp_path):
    with pytest.raises(TypeError):
        write_toml_document(tmp_path / "a.toml", {"modules": {"m": 3}}, ["# h"])


def test_a_top_level_value_that_is_not_a_table_raises(tmp_path):
    with pytest.raises(TypeError):
        write_toml_document(tmp_path / "a.toml", {"modules": "flat"}, ["# h"])


def test_sub_tables_of_tool_become_platform_tables(tmp_path):
    target = tmp_path / "a.toml"
    write_toml_document(target, {"tool": {"windows": {"cmake_exe": "C:\cmake\cmake.exe"}}}, ["# h"])
    assert "[tool.windows]" in target.read_text(encoding="utf-8")
    assert 'cmake_exe = "C:/cmake/cmake.exe"' in target.read_text(encoding="utf-8")
