"""Root discovery: either marker finds a checkout, and says which one it was."""

import pytest

from sushicore.module_config import ModuleConfig
from sushicore.profile import RELEASE_MANIFEST, ModuleProfile

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
