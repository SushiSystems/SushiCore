"""Root discovery, and which shared config a module CLI reads from its workspace."""

import pytest

from sushicore.module_config import ModuleConfig
from sushicore.profile import RELEASE_MANIFEST, ModuleProfile
from sushicore.workspace import (
    LEGACY_SHARED_CONFIG,
    WORKSPACE_MARKER,
    workspace_file,
    write_link,
)

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


def test_the_shared_config_is_the_workspace_file(tmp_path, monkeypatch):
    """A workspace carrying workspace.toml hands that file to the module CLI."""
    _workspace(tmp_path, new=True)
    monkeypatch.setenv("SUSHISTACK_HOME", str(tmp_path))
    module = ModuleConfig(PROFILE)
    assert module._shared_config_local() == workspace_file(tmp_path)


def test_an_unupgraded_workspace_falls_back_to_the_old_file(tmp_path, monkeypatch):
    """Before any `hub` command upgrades it, the pre-2026-09-22 path is read."""
    _workspace(tmp_path, legacy=True)
    monkeypatch.setenv("SUSHISTACK_HOME", str(tmp_path))
    module = ModuleConfig(PROFILE)
    assert module._shared_config_local() == tmp_path / LEGACY_SHARED_CONFIG


def test_the_new_file_wins_when_both_exist(tmp_path, monkeypatch):
    """An upgraded workspace that kept its old file still reads the new one."""
    _workspace(tmp_path, new=True, legacy=True)
    monkeypatch.setenv("SUSHISTACK_HOME", str(tmp_path))
    module = ModuleConfig(PROFILE)
    assert module._shared_config_local() == workspace_file(tmp_path)


def test_a_workspace_with_neither_file_shares_nothing(tmp_path, monkeypatch):
    """A marked workspace that holds no config hands the module CLI nothing."""
    _workspace(tmp_path)
    monkeypatch.setenv("SUSHISTACK_HOME", str(tmp_path))
    module = ModuleConfig(PROFILE)
    assert module._shared_config_local() is None


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
