# test_module_config.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Root discovery, and which shared config a module CLI reads from its workspace."""

import pytest

from sushicore.config_base import ToolConfig
from sushicore.module_config import ModuleConfig
from sushicore.profile import RELEASE_MANIFEST, ModuleProfile
from sushicore.workspace import (
    LEGACY_SHARED_CONFIG,
    WORKSPACE_MARKER,
    workspace_file,
    write_link,
)


pytestmark = pytest.mark.medium

PROFILE = ModuleProfile(name="SushiEngine", program="se", env_prefix="SE")


def _nested(root):
    """Create and return a directory a command could be invoked from."""
    deep = root / "src" / "kernels"
    deep.mkdir(parents=True)
    return deep


def test_a_release_manifest_alone_marks_a_binary_root(tmp_path):
    (tmp_path / RELEASE_MANIFEST).write_text('{"product": "sushiengine"}')
    module = ModuleConfig(PROFILE)
    assert module.find_project_root(_nested(tmp_path)) == tmp_path.resolve()
    assert module.presence(tmp_path) == "binary"


def test_a_root_marker_alone_marks_a_source_root(tmp_path):
    (tmp_path / "CMakeLists.txt").write_text("")
    module = ModuleConfig(PROFILE)
    assert module.find_project_root(_nested(tmp_path)) == tmp_path.resolve()
    assert module.presence(tmp_path) == "source"


def test_presence_falls_back_to_the_discovered_root(tmp_path, monkeypatch):
    (tmp_path / RELEASE_MANIFEST).write_text("{}")
    monkeypatch.chdir(_nested(tmp_path))
    assert ModuleConfig(PROFILE).presence() == "binary"


def test_a_tree_with_neither_marker_names_both_markers(tmp_path):
    with pytest.raises(SystemExit) as raised:
        ModuleConfig(PROFILE).find_project_root(tmp_path)
    message = str(raised.value)
    assert "CMakeLists.txt" in message
    assert RELEASE_MANIFEST in message


def _workspace(root, *, new: bool = False, legacy: bool = False):
    """Build a workspace root carrying the new file, the old one, or neither."""
    (root / WORKSPACE_MARKER).mkdir(exist_ok=True)
    if new:
        workspace_file(root).write_text('[tool]\ntoolchain = "acpp"\n', encoding="utf-8")
    if legacy:
        legacy_path = root / LEGACY_SHARED_CONFIG
        legacy_path.parent.mkdir(parents=True, exist_ok=True)
        legacy_path.write_text('[tool]\ntoolchain = "intel-llvm"\n', encoding="utf-8")
    return root


@pytest.fixture
def checkout(tmp_path, monkeypatch):
    """Return a module checkout the working directory sits in, and no workspace link to it."""
    root = tmp_path / "module"
    root.mkdir()
    (root / "CMakeLists.txt").write_text("")
    monkeypatch.chdir(root)
    monkeypatch.delenv("SUSHISTACK_HOME", raising=False)
    return root.resolve()


@pytest.fixture
def workspace_root(tmp_path, monkeypatch):
    """Return a workspace root that SUSHISTACK_HOME names."""
    root = tmp_path / "workspace"
    root.mkdir()
    monkeypatch.setenv("SUSHISTACK_HOME", str(root))
    return root.resolve()


def _layers(checkout, *shared):
    """Return the config files a module layers: its own file, the shared ones, its local file."""
    cli = checkout / "cli"
    return [cli / "config.toml", *shared, cli / "config.local.toml"]


def test_the_shared_config_is_the_workspace_file(checkout, workspace_root):
    """A workspace carrying workspace.toml hands that file to the module CLI."""
    _workspace(workspace_root, new=True)
    assert ModuleConfig(PROFILE).sources() == _layers(checkout, workspace_file(workspace_root))


def test_an_unupgraded_workspace_falls_back_to_the_old_file(checkout, workspace_root):
    """Before any `hub` command upgrades it, the pre-2026-09-22 path is read."""
    _workspace(workspace_root, legacy=True)
    assert ModuleConfig(PROFILE).sources() == _layers(
        checkout, workspace_root / LEGACY_SHARED_CONFIG)


def test_the_new_file_wins_when_both_exist(checkout, workspace_root):
    """An upgraded workspace that kept its old file still reads the new one."""
    _workspace(workspace_root, new=True, legacy=True)
    assert ModuleConfig(PROFILE).sources() == _layers(checkout, workspace_file(workspace_root))


def test_a_workspace_with_neither_file_shares_nothing(checkout, workspace_root):
    """A marked workspace that holds no config hands the module CLI nothing."""
    _workspace(workspace_root)
    assert ModuleConfig(PROFILE).sources() == _layers(checkout)


def _write_tool_table(path, **fields):
    """Write a config file whose ``[tool]`` table holds *fields*."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["[tool]", *(f'{name} = "{value}"' for name, value in fields.items())]
    path.write_text(chr(10).join(lines), encoding="utf-8")


def test_load_layers_repo_config_shared_config_local_config_and_environment_in_order(
        checkout, workspace_root, monkeypatch):
    """Each later layer wins on a field it repeats, and the environment wins over all files."""
    _workspace(workspace_root, new=True)
    _write_tool_table(checkout / "cli" / "config.toml",
                      cxx="repo", generator="repo", vcpkg_root="repo", ninja_exe="repo")
    _write_tool_table(workspace_file(workspace_root),
                      cxx="shared", generator="shared", ninja_exe="shared")
    _write_tool_table(checkout / "cli" / "config.local.toml", cxx="local", ninja_exe="local")
    monkeypatch.setenv("SE_NINJA", "environment")
    loaded = ModuleConfig(PROFILE).load(ToolConfig)
    assert (loaded.cxx, loaded.generator, loaded.vcpkg_root, loaded.ninja_exe) == (
        "local", "shared", "repo", "environment")


def test_workspace_home_follows_the_link_pointer(tmp_path, monkeypatch):
    monkeypatch.delenv("SUSHISTACK_HOME", raising=False)
    ws = tmp_path / "ws"
    (ws / WORKSPACE_MARKER).mkdir(parents=True)
    mod = tmp_path / "elsewhere" / "mod"
    (mod / "cli").mkdir(parents=True)
    (mod / "CMakeLists.txt").write_text("")
    write_link(mod / "cli", ws)
    assert ModuleConfig(PROFILE).workspace_home(mod) == ws.resolve()


def test_a_stale_link_pointer_falls_back_to_the_walk_up(tmp_path, monkeypatch):
    monkeypatch.delenv("SUSHISTACK_HOME", raising=False)
    gone = tmp_path / "gone"
    (gone / WORKSPACE_MARKER).mkdir(parents=True)
    outer = tmp_path / "outer"
    (outer / WORKSPACE_MARKER).mkdir(parents=True)
    mod = outer / "mod"
    (mod / "cli").mkdir(parents=True)
    write_link(mod / "cli", gone)
    (gone / WORKSPACE_MARKER).rmdir()
    assert ModuleConfig(PROFILE).workspace_home(mod) == outer.resolve()


def test_environment_beats_the_link_pointer(tmp_path, monkeypatch):
    other = tmp_path / "other"
    other.mkdir()
    monkeypatch.setenv("SUSHISTACK_HOME", str(other))
    ws = tmp_path / "ws"
    (ws / WORKSPACE_MARKER).mkdir(parents=True)
    mod = tmp_path / "mod"
    (mod / "cli").mkdir(parents=True)
    (mod / "CMakeLists.txt").write_text("")
    write_link(mod / "cli", ws)
    assert ModuleConfig(PROFILE).workspace_home(mod) == other.resolve()
