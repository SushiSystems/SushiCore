# test_dependency_source.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The promises every dependency source keeps, in memory and over fragment files."""

from __future__ import annotations

import json

import pytest

from sushicore.provision.fragments import (
    Dependency,
    IDependencySource,
    TomlDependencySource,
)
from sushicore.provision.fragments_memory import InMemoryDependencySource

K_DIGEST = "3f" * 32
K_OWNER = "sushidsp"

#: Declared in this order; the platform columns say who needs a package from each.
K_DEPENDENCIES = (
    Dependency(name="cmake", linux_apt=["cmake"], sha256={"windows": K_DIGEST}, owner=K_OWNER),
    Dependency(name="gtest", linux_apt=["libgtest-dev"], windows_vcpkg=["gtest"], owner=K_OWNER),
    Dependency(name="cuda-lib", gpu_only=True, linux_apt=["nvcc"], owner=K_OWNER),
    Dependency(name="docs-only", owner=K_OWNER),
)


def _fragment_text(dependencies: tuple[Dependency, ...], depends_on: list[str]) -> str:
    """Return the fragment file that declares *dependencies* and the modules they build on."""
    text = f"[module]\ndepends_on = {json.dumps(depends_on)}\n"
    for dep in dependencies:
        text += (f"[{dep.name}]\nrequired = {json.dumps(dep.required)}\n"
                 f"gpu_only = {json.dumps(dep.gpu_only)}\n"
                 f"linux_apt = {json.dumps(dep.linux_apt)}\n"
                 f"windows_vcpkg = {json.dumps(dep.windows_vcpkg)}\n")
        if dep.sha256:
            text += f"sha256 = {{ windows = {json.dumps(dep.sha256['windows'])} }}\n"
    return text


class DependencySourceContract:
    """The promises every :class:`IDependencySource` keeps; a subclass supplies the source."""

    def test_all_returns_every_declaration_whatever_the_platform(self, source):
        assert [dep.name for dep in source.all()] == [
            "cmake", "gtest", "cuda-lib", "docs-only"]

    @pytest.mark.parametrize(("platform", "gpu", "expected"), [
        ("linux", False, ["cmake", "gtest"]),
        ("linux", True, ["cmake", "gtest", "cuda-lib"]),
        ("windows", False, ["gtest"]),
    ])
    def test_selected_keeps_what_the_platform_has_a_package_for(
            self, source, platform, gpu, expected):
        assert [dep.name for dep in source.selected(platform, gpu)] == expected

    def test_digests_name_each_pinned_dependency_of_a_platform(self, source):
        assert source.digests("windows") == {"cmake": K_DIGEST}

    def test_digests_are_empty_for_a_platform_with_no_pin(self, source):
        assert source.digests("linux") == {}

    def test_depends_on_lists_the_modules_an_owner_builds_on(self, source):
        source.all()
        assert source.depends_on(K_OWNER) == ["sushilog"]

    def test_depends_on_is_empty_for_an_owner_that_declares_none(self, source):
        source.all()
        assert source.depends_on("nobody") == []


@pytest.mark.small
class TestInMemoryDependencySourceKeepsTheDependencySourceContract(DependencySourceContract):
    """The source that serves a list given in memory."""

    @pytest.fixture
    def source(self) -> IDependencySource:
        return InMemoryDependencySource(K_DEPENDENCIES, {K_OWNER: ["sushilog"]})


@pytest.mark.medium
class TestTomlDependencySourceKeepsTheDependencySourceContract(DependencySourceContract):
    """The source that reads a fragment file from a folder."""

    @pytest.fixture
    def source(self, tmp_path, recording_console) -> IDependencySource:
        path = tmp_path / "sushistack.deps.toml"
        path.write_text(_fragment_text(K_DEPENDENCIES, ["sushilog"]), encoding="utf-8")
        return TomlDependencySource([(path, K_OWNER)])
