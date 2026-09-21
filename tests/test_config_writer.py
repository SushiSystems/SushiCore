"""The config writer keeps the tables it was not asked to write."""

from __future__ import annotations

from sushicore.config_base import write_tool_section
from sushicore.workspace import read_toml


def test_a_sibling_table_survives_a_tool_write(tmp_path):
    """Writing [tool] leaves an unrelated [modules] table intact."""
    target = tmp_path / "workspace.toml"
    target.write_text('[modules]\nsushiai = "D:/Projects/sushiai"\n\n[tool]\ngenerator = "Ninja"\n',
                      encoding="utf-8")
    write_tool_section(target, {"toolchain": "intel-llvm"}, ["# header"])
    doc = read_toml(target)
    assert doc["modules"] == {"sushiai": "D:/Projects/sushiai"}
    assert doc["tool"]["toolchain"] == "intel-llvm"
    assert doc["tool"]["generator"] == "Ninja"


def test_the_platform_sub_table_still_survives(tmp_path):
    """The existing guarantee holds: [tool.<platform>] is preserved verbatim."""
    target = tmp_path / "workspace.toml"
    target.write_text('[tool]\n[tool.windows]\ngenerator = "Ninja"\n', encoding="utf-8")
    write_tool_section(target, {"toolchain": "acpp"}, ["# header"])
    doc = read_toml(target)
    assert doc["tool"]["windows"]["generator"] == "Ninja"
    assert doc["tool"]["toolchain"] == "acpp"


def test_a_non_string_in_a_sibling_table_is_refused(tmp_path):
    """A value the emitter cannot render raises rather than disappearing."""
    import pytest
    target = tmp_path / "workspace.toml"
    target.write_text('[counts]\nmodules = 4\n\n[tool]\n', encoding="utf-8")
    with pytest.raises(TypeError):
        write_tool_section(target, {"toolchain": "acpp"}, ["# header"])
