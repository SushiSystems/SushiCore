# test_diag.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests the config and env diagnostics a CLI offers."""

import pytest

from sushicore.diag import Diagnostics
from sushicore.profile import ModuleProfile

pytestmark = pytest.mark.small


class _Printer:
    def __init__(self):
        self.printed = []

    def print(self, renderable):
        self.printed.append(renderable)


class _Console:
    accent = "bold"

    def __init__(self):
        self.lines = []
        self.console = _Printer()

    def header(self, title):
        self.lines.append(("header", title))

    def info(self, message):
        self.lines.append(("info", message))

    def error(self, message):
        self.lines.append(("error", message))


class _Config:
    def __init__(self, root):
        self._root = root

    def find_project_root(self, start=None):
        return self._root

    def load_config(self):
        return object()


def _diagnostics(tmp_path, build_env):
    console = _Console()
    profile = ModuleProfile(name="SushiTest", program="st", env_prefix="ST")
    return Diagnostics(profile=profile, console=console, config=_Config(tmp_path),
                       build_env=build_env), console


def test_env_without_a_build_environment_fails_with_one_line(tmp_path):
    diagnostics, console = _diagnostics(tmp_path, None)
    assert diagnostics.env_dump() == 1
    assert console.lines == [("error", "st has no build environment to dump.")]


def test_env_shows_only_build_relevant_variables_unless_asked(tmp_path):
    seen = {}

    def build_env(cfg, build_dir):
        seen["build_dir"] = build_dir
        return {"PATH": "/bin", "UNRELATED_THING": "x"}

    diagnostics, console = _diagnostics(tmp_path, build_env)
    assert diagnostics.env_dump() == 0
    assert seen["build_dir"] == tmp_path / "build"
    assert console.lines[-1] == ("info", "1 of 2 variables shown (build-relevant; use --all for everything)")
    assert diagnostics.env_dump(show_all=True) == 0
    assert console.lines[-1] == ("info", "2 of 2 variables shown")


from dataclasses import dataclass


@dataclass
class _Settings:
    cxx: str = ""
    generator: str = "Ninja"
    vcpkg_root: str = ""


class _LayeredConfig:
    """A config module whose files sit in a directory and in a linked workspace."""

    Config = _Settings
    _ENV_OVERRIDES = {"vcpkg_root": "ST_TEST_VCPKG"}

    def __init__(self, root, with_sources):
        self._root = root
        if with_sources:
            self.sources = lambda: [root / "cli" / "config.toml", root.parent / "ws" / "workspace.toml",
                                    root / "cli" / "config.local.toml"]

    def find_project_root(self, start=None):
        return self._root

    def config_dir(self, root=None):
        return self._root / "cli"

    def load_config(self):
        return _Settings(cxx="clang", generator="Ninja", vcpkg_root="/v")


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _source_column(console):
    table = console.console.printed[0]
    names = table.columns[0]._cells
    sources = table.columns[2]._cells
    return dict(zip(names, sources))


def _show(tmp_path, with_sources):
    root = tmp_path / "module"
    _write(root / "cli" / "config.toml", '[tool]\ngenerator = "Ninja"\ncxx = "gcc"\n')
    _write(root / "cli" / "config.local.toml", '[tool]\ncxx = "clang"\n')
    _write(tmp_path / "ws" / "workspace.toml", '[tool]\ngenerator = "Make"\nvcpkg_root = "/w"\n')
    console = _Console()
    profile = ModuleProfile(name="SushiTest", program="st", env_prefix="ST")
    Diagnostics(profile=profile, console=console,
                config=_LayeredConfig(root, with_sources)).config_show()
    return _source_column(console)


def test_a_value_set_in_the_local_file_names_the_local_file(tmp_path):
    assert _show(tmp_path, with_sources=False)["cxx"] == "config.local.toml"


def test_a_value_from_the_linked_workspace_names_the_workspace(tmp_path):
    column = _show(tmp_path, with_sources=True)
    assert column["generator"] == "workspace"
    assert column["cxx"] == "config.local.toml"


def test_a_value_set_nowhere_is_the_default(tmp_path):
    assert _show(tmp_path, with_sources=True)["vcpkg_root"] == "workspace"
    root = tmp_path / "other"
    console = _Console()
    profile = ModuleProfile(name="SushiTest", program="st", env_prefix="ST")
    Diagnostics(profile=profile, console=console, config=_LayeredConfig(root, False)).config_show()
    assert _source_column(console)["generator"] == "default"
