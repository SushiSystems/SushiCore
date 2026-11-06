# test_toml_writer.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The TOML writer renders the tables it is given and refuses what it cannot keep."""

import pytest

from sushicore.toml_writer import render_toml_document, write_toml_document
from sushicore.workspace import read_toml


@pytest.mark.small
def test_it_renders_tool_first_and_the_other_tables_sorted():
    """The tool table comes first and every other table follows in name order."""
    body = render_toml_document(
        {"workspace": {"version": "1"}, "tool": {"toolchain": "acpp"}, "modules": {"a": "b"}},
        ["# header"])
    assert body.index("[tool]") < body.index("[modules]") < body.index("[workspace]")


@pytest.mark.small
def test_backslashes_in_a_table_value_become_forward_slashes():
    """A Windows path in a table is written with forward slashes."""
    body = render_toml_document({"modules": {"sushiai": r"D:\Projects\sushiai"}}, ["# h"])
    assert 'sushiai = "D:/Projects/sushiai"' in body


@pytest.mark.small
def test_sub_tables_of_tool_become_platform_tables():
    """A sub-table of tool is written as a [tool.<platform>] table."""
    body = render_toml_document({"tool": {"windows": {"cmake_exe": "c/cmake.exe"}}}, ["# h"])
    assert "[tool.windows]" in body


@pytest.mark.small
def test_backslashes_in_a_platform_table_value_become_forward_slashes():
    """A Windows path in a [tool.<platform>] table is written with forward slashes."""
    body = render_toml_document(
        {"tool": {"windows": {"cmake_exe": r"C:\cmake\cmake.exe"}}}, ["# h"])
    assert 'cmake_exe = "C:/cmake/cmake.exe"' in body


@pytest.mark.medium
def test_what_it_writes_reads_back_as_the_same_tables(tmp_path):
    """A document written to disk reads back as the tables that were given."""
    target = tmp_path / "a.toml"
    write_toml_document(target, {"tool": {"x": "1", "flag": True}, "modules": {"m": "p"}}, ["# h"])
    assert read_toml(target) == {"tool": {"x": "1", "flag": True}, "modules": {"m": "p"}}


@pytest.mark.small
def test_a_value_that_is_not_a_string_in_a_table_raises_instead_of_vanishing():
    """A non-string value in a table raises TypeError."""
    with pytest.raises(TypeError):
        render_toml_document({"modules": {"m": 3}}, ["# h"])


@pytest.mark.small
def test_a_top_level_value_that_is_not_a_table_raises():
    """A top-level value that is not a table raises TypeError."""
    with pytest.raises(TypeError):
        render_toml_document({"modules": "flat"}, ["# h"])
