# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the dependency root resolution."""

from __future__ import annotations

from pathlib import Path

from sushicore.provision import home


def test_default_root_is_in_the_user_home(monkeypatch):
    monkeypatch.delenv(home.ENV_HOME, raising=False)
    home.bind_root(None)
    assert home.root() == Path.home() / ".sushisystems"


def test_env_var_wins_and_is_expanded_and_absolute(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv(home.ENV_HOME, "relative/deps")
    home.bind_root(None)
    assert home.root() == (tmp_path / "relative" / "deps").resolve()


def test_bound_root_wins_over_env(provision_home, tmp_path):
    bound = tmp_path / "bound"
    home.bind_root(lambda: bound)
    assert home.root() == bound.resolve()


def test_subdirectories_hang_off_the_root(provision_home):
    assert home.toolchains_dir() == provision_home.resolve() / "toolchains"
    assert home.tools_dir() == provision_home.resolve() / "tools"
    assert home.vcpkg_dir() == provision_home.resolve() / "vcpkg"
    assert home.ur_dir() == provision_home.resolve() / "ur"
    assert home.build_dir() == provision_home.resolve() / "build"


def test_no_legacy_root_outside_a_workspace(provision_home):
    assert home.legacy_roots() == []
    assert home.search_roots() == [home.root()]


def test_workspace_dependencies_is_a_legacy_root(provision_home, tmp_path, monkeypatch):
    ws = tmp_path / "ws"
    (ws / ".sushistack").mkdir(parents=True)
    (ws / "dependencies").mkdir()
    monkeypatch.chdir(ws)
    assert home.legacy_roots() == [(ws / "dependencies").resolve()]
    assert home.search_roots() == [home.root(), (ws / "dependencies").resolve()]


def test_legacy_env_override_is_a_legacy_root(provision_home, tmp_path, monkeypatch):
    legacy = tmp_path / "old"
    legacy.mkdir()
    monkeypatch.setenv("SUSHISTACK_DEPS_DIR", str(legacy))
    assert home.legacy_roots() == [legacy.resolve()]


def test_the_bound_root_is_never_its_own_legacy_root(provision_home, tmp_path, monkeypatch):
    ws = tmp_path / "ws"
    (ws / ".sushistack").mkdir(parents=True)
    (ws / "dependencies").mkdir()
    monkeypatch.chdir(ws)
    home.bind_root(lambda: ws / "dependencies")
    assert home.legacy_roots() == []


def test_an_ordinary_directory_is_removable(tmp_path):
    target = tmp_path / "deps"
    target.mkdir()
    assert home.is_removable_root(target) is True


def test_the_users_home_directory_is_refused():
    assert home.is_removable_root(Path.home()) is False


def test_a_filesystem_anchor_is_refused(tmp_path):
    assert home.is_removable_root(Path(tmp_path.anchor)) is False


def test_the_current_directory_is_refused(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert home.is_removable_root(tmp_path) is False


def test_an_ancestor_of_the_current_directory_is_refused(tmp_path, monkeypatch):
    child = tmp_path / "a" / "b"
    child.mkdir(parents=True)
    monkeypatch.chdir(child)
    assert home.is_removable_root(tmp_path) is False


def test_a_directory_holding_a_git_marker_is_refused(tmp_path):
    target = tmp_path / "repo"
    (target / ".git").mkdir(parents=True)
    assert home.is_removable_root(target) is False


def test_a_directory_holding_a_workspace_marker_is_refused(tmp_path):
    target = tmp_path / "workspace"
    (target / ".sushistack").mkdir(parents=True)
    assert home.is_removable_root(target) is False


def test_env_var_with_tilde_is_expanded(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv(home.ENV_HOME, "~/x")
    home.bind_root(None)
    assert home.root() == (Path.home() / "x").resolve()
    assert home.root() == (tmp_path / "x").resolve()
