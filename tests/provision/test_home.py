# test_home.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the dependency root and the legacy trees read beside it."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.provision import home
from sushicore.workspace import WORKSPACE_MARKER


K_ROOT = Path("/machine/root").resolve()
K_USER = Path("/users/me")
K_WORK = Path("/work").resolve()
K_WORKSPACE = Path("/workspace").resolve()
K_LEGACY = Path("/legacy").resolve()


def _legacy(environ, *, workspace=None, existing=(), current=K_ROOT):
    """Return the legacy roots for *environ*, a workspace walk giving *workspace*, and *existing* folders."""
    return home.legacy_roots(environ=environ, cwd=K_WORK, current=current,
                             is_dir=lambda path: path in existing,
                             workspace_of=lambda start: workspace)


def _removable(path, *, marker=None, cwd=K_WORK):
    """Return whether *path* is removable when only the folder named *marker* exists as a marker."""
    return home.is_removable_root(path, user_home=K_USER, cwd=cwd,
                                  exists=lambda candidate: candidate.name == marker)


@pytest.mark.small
def test_default_root_is_in_the_user_home():
    """Check that default root is in the user home."""
    assert home.root(environ={}, user_home=K_USER) == K_USER / ".sushisystems"


@pytest.mark.small
def test_env_var_wins_and_is_expanded_and_absolute():
    """Check that env var wins and is expanded and absolute."""
    root = home.root(environ={home.ENV_HOME: "relative/deps"}, cwd=K_WORK)
    assert root == (K_WORK / "relative" / "deps").resolve()


@pytest.mark.small
def test_bound_root_wins_over_env():
    """Check that a bound provider wins over the env var."""
    root = home.root(environ={home.ENV_HOME: "/from/env"}, bound=lambda: Path("/bound"))
    assert root == Path("/bound").resolve()


@pytest.mark.small
@pytest.mark.parametrize("name", ["toolchains", "tools", "vcpkg", "ur", "build"])
def test_subdirectories_hang_off_the_root(name):
    """Check that each subdirectory is named for its purpose and hangs off the given root."""
    assert getattr(home, f"{name}_dir")(K_ROOT) == K_ROOT / name


@pytest.mark.small
def test_no_legacy_root_outside_a_workspace():
    """Check that no legacy root exists without an override or a workspace."""
    assert _legacy({}) == []


@pytest.mark.small
def test_the_search_roots_are_the_root_alone_without_a_legacy_root():
    """Check that the search starts and ends at the root when no legacy root exists."""
    assert home.search_roots(current=K_ROOT, legacy=[]) == [K_ROOT]


@pytest.mark.small
def test_workspace_dependencies_is_a_legacy_root():
    """Check that the workspace's dependencies folder is a legacy root."""
    dependencies = (K_WORKSPACE / "dependencies").resolve()
    assert _legacy({}, workspace=K_WORKSPACE, existing={dependencies}) == [dependencies]


@pytest.mark.small
def test_the_search_roots_list_the_legacy_roots_after_the_root():
    """Check that the legacy roots follow the root in lookup order."""
    assert home.search_roots(current=K_ROOT, legacy=[K_LEGACY]) == [K_ROOT, K_LEGACY]


@pytest.mark.small
def test_legacy_env_override_is_a_legacy_root():
    """Check that the legacy env override is a legacy root."""
    assert _legacy({"SUSHISTACK_DEPS_DIR": str(K_LEGACY)}, existing={K_LEGACY}) == [K_LEGACY]


@pytest.mark.small
def test_a_legacy_root_that_is_no_folder_is_left_out():
    """Check that a candidate that is not a folder is not a legacy root."""
    assert _legacy({"SUSHISTACK_DEPS_DIR": str(K_LEGACY)}, existing=set()) == []


@pytest.mark.small
def test_the_bound_root_is_never_its_own_legacy_root():
    """Check that the current root is never its own legacy root."""
    dependencies = (K_WORKSPACE / "dependencies").resolve()
    legacy = _legacy({}, workspace=K_WORKSPACE, existing={dependencies}, current=dependencies)
    assert legacy == []


@pytest.mark.small
def test_an_ordinary_directory_is_removable():
    """Check that an ordinary directory is removable."""
    assert _removable(Path("/machine/deps")) is True


@pytest.mark.small
def test_the_users_home_directory_is_refused():
    """Check that the users home directory is refused."""
    assert _removable(K_USER) is False


@pytest.mark.small
def test_a_filesystem_anchor_is_refused():
    """Check that a filesystem anchor is refused."""
    assert _removable(Path(K_ROOT.anchor)) is False


@pytest.mark.small
def test_the_current_directory_is_refused():
    """Check that the current directory is refused."""
    assert _removable(K_WORK, cwd=K_WORK) is False


@pytest.mark.small
def test_an_ancestor_of_the_current_directory_is_refused():
    """Check that an ancestor of the current directory is refused."""
    assert _removable(K_WORK, cwd=K_WORK / "a" / "b") is False


@pytest.mark.small
def test_a_directory_holding_a_git_marker_is_refused():
    """Check that a directory holding a git marker is refused."""
    assert _removable(Path("/machine/repo"), marker=".git") is False


@pytest.mark.small
def test_a_directory_holding_a_workspace_marker_is_refused():
    """Check that a directory holding a workspace marker is refused."""
    assert _removable(Path("/machine/workspace"), marker=WORKSPACE_MARKER) is False


@pytest.mark.small
def test_env_var_with_tilde_is_expanded():
    """Check that a leading tilde in the env var stands for the user home."""
    assert home.root(environ={home.ENV_HOME: "~/x"}, user_home=K_USER) == (K_USER / "x").resolve()


@pytest.mark.small
def test_found_vcpkg_dir_prefers_an_existing_legacy_tree():
    """Check that a vcpkg tree in a legacy root is found when the current root has none."""
    found = home.found_vcpkg_dir([K_ROOT, K_LEGACY], is_dir=lambda path: path == K_LEGACY / "vcpkg")
    assert found == K_LEGACY / "vcpkg"


@pytest.mark.small
def test_found_vcpkg_dir_defaults_to_the_current_root():
    """Check that no tree anywhere gives the current root's vcpkg folder."""
    assert home.found_vcpkg_dir([K_ROOT], is_dir=lambda path: False) == K_ROOT / "vcpkg"


@pytest.mark.small
def test_sources_dir_is_under_the_root():
    """Check that the fetched Sushi sources sit in <root>/sources."""
    assert home.sources_dir(K_ROOT) == K_ROOT / "sources"
