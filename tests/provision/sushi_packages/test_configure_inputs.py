# test_configure_inputs.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the hash of a library's configure inputs."""

from __future__ import annotations

import os
import subprocess

import pytest

from sushicore.provision.sushi_packages.configure_inputs import (
    ConfigureInputs,
    MemoryCMakeVersion,
    MemoryVcpkgHead,
    probe_cmake_version,
    probe_vcpkg_head,
)
from sushicore.provision.sushi_packages.package_error import PackageError

pytestmark = pytest.mark.medium


def _inputs(cmake="3.28.1", head="h1") -> ConfigureInputs:
    """Return a reader whose probes answer *cmake* and *head*."""
    return ConfigureInputs(MemoryCMakeVersion(cmake), MemoryVcpkgHead(head))


def _read(checkout, reader=None, triplet="x64-windows", vcpkg=None):
    """Return the inputs hash of *checkout*."""
    return (reader or _inputs()).read(checkout, vcpkg, triplet)


def _git(folder, *arguments) -> str:
    """Run git in *folder* and return what it prints."""
    done = subprocess.run(["git", "-C", str(folder), "-c", "user.name=t",
                           "-c", "user.email=t@example.com", *arguments],
                          capture_output=True, text=True, check=True)
    return done.stdout.strip()


def _script(folder, text):
    """Write an executable that prints *text* and return its path as text."""
    windows = os.name == "nt"
    path = folder / ("fake_cmake.cmd" if windows else "fake_cmake")
    shown = f"echo {text}\n" if text else ""
    path.write_text(("@echo off\n" if windows else "#!/bin/sh\n") + shown, encoding="utf-8")
    path.chmod(0o755)
    return str(path)


def test_a_missing_file_hashes_as_absent(tmp_path):
    """Check that a missing input file reads as absent, which an empty file does not."""
    absent = _read(tmp_path)
    (tmp_path / "vcpkg.json").write_text("", encoding="utf-8")
    assert _read(tmp_path) != absent


@pytest.mark.parametrize("name", [
    "cli/config.local.toml", "vcpkg.json", "vcpkg-configuration.json"])
def test_each_input_file_changes_the_hash(tmp_path, name):
    """Check that creating or editing an input file changes the hash."""
    before = _read(tmp_path)
    path = tmp_path / name
    path.parent.mkdir(exist_ok=True)
    path.write_text("a", encoding="utf-8")
    created = _read(tmp_path)
    path.write_text("b", encoding="utf-8")
    assert len({before, created, _read(tmp_path)}) == 3


def test_the_vcpkg_head_changes_the_hash(tmp_path):
    """Check that another vcpkg commit gives another hash."""
    base = _read(tmp_path, vcpkg=tmp_path)
    assert _read(tmp_path, _inputs(head="h2"), vcpkg=tmp_path) != base


def test_the_triplet_changes_the_hash(tmp_path):
    """Check that another triplet gives another hash."""
    base = _read(tmp_path, vcpkg=tmp_path)
    assert _read(tmp_path, triplet="x64-linux", vcpkg=tmp_path) != base


def test_a_patch_release_of_cmake_keeps_the_hash(tmp_path):
    """Check that a patch release of CMake leaves the hash as it was."""
    assert _read(tmp_path, _inputs(cmake="3.28.9")) == _read(tmp_path)


def test_a_minor_release_of_cmake_changes_the_hash(tmp_path):
    """Check that a minor release of CMake gives another hash."""
    assert _read(tmp_path, _inputs(cmake="3.29.0")) != _read(tmp_path)


def test_the_vcpkg_head_is_the_commit_of_the_tree(tmp_path):
    """Check that the head of a vcpkg tree is the commit git names."""
    _git(tmp_path, "init")
    _git(tmp_path, "commit", "--allow-empty", "-m", "first")
    assert probe_vcpkg_head(tmp_path) == _git(tmp_path, "rev-parse", "HEAD")


def test_a_folder_with_no_repository_has_no_vcpkg_head(tmp_path):
    """Check that a folder git cannot read gives an empty head."""
    assert probe_vcpkg_head(tmp_path) == ""


@pytest.mark.parametrize("line, version", [
    ("cmake version 3.28.1", "3.28.1"),
    ("cmake version 3.30", "3.30"),
])
def test_the_cmake_version_is_read_from_its_version_line(tmp_path, line, version):
    """Check that the number after the program name is the version."""
    assert probe_cmake_version(_script(tmp_path, line)) == version


def test_a_cmake_that_prints_no_version_raises(tmp_path):
    """Check that an executable printing no version is refused."""
    with pytest.raises(PackageError, match="no version"):
        probe_cmake_version(_script(tmp_path, ""))
