# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the fragment source taking an explicit list of files."""

from __future__ import annotations

from sushicore.provision.fragments import SHARED_OWNER, TomlDependencySource


def _write(path, body):
    path.write_text(body, encoding="utf-8")
    return path


def test_source_reads_only_the_files_it_is_given(tmp_path, recording_console):
    mine = _write(tmp_path / "mine.deps.toml", '[gtest]\ndescription = "t"\nrequired = false\n'
                  'linux_apt = ["libgtest-dev"]\nwindows_vcpkg = ["gtest"]\n')
    source = TomlDependencySource([(mine, "sushitrack")])
    deps = source.all()
    assert [d.name for d in deps] == ["gtest"]
    assert deps[0].owner == "sushitrack"


def test_same_named_deps_merge_across_files(tmp_path, recording_console):
    a = _write(tmp_path / "a.deps.toml", '[x]\ndescription = "a"\nrequired = false\n'
               'linux_apt = ["p1"]\nwindows_vcpkg = []\n')
    b = _write(tmp_path / "b.deps.toml", '[x]\ndescription = "b"\nrequired = true\n'
               'linux_apt = ["p2"]\nwindows_vcpkg = []\n')
    (dep,) = TomlDependencySource([(a, SHARED_OWNER), (b, "m")]).all()
    assert dep.required is True
    assert dep.linux_apt == ["p1", "p2"]
