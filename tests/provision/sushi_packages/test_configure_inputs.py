# test_configure_inputs.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests for the hash of a library's configure inputs."""

from __future__ import annotations

import pytest

from sushicore.provision.sushi_packages.configure_inputs import ConfigureInputs

pytestmark = pytest.mark.medium


def _inputs(cmake="3.28.1", head="h1") -> ConfigureInputs:
    """Return a reader whose probes answer *cmake* and *head*."""
    return ConfigureInputs(lambda: cmake, lambda _root: head)


def _read(checkout, reader=None, triplet="x64-windows", vcpkg=None):
    """Return the inputs hash of *checkout*."""
    return (reader or _inputs()).read(checkout, vcpkg, triplet)


def test_a_missing_file_hashes_as_absent(tmp_path):
    """Check that a checkout with none of the files reads without raising."""
    assert _read(tmp_path)


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


def test_the_vcpkg_head_and_the_triplet_change_the_hash(tmp_path):
    """Check that another vcpkg commit or triplet gives another hash."""
    base = _read(tmp_path, vcpkg=tmp_path)
    assert _read(tmp_path, _inputs(head="h2"), vcpkg=tmp_path) != base
    assert _read(tmp_path, triplet="x64-linux", vcpkg=tmp_path) != base


def test_only_the_minor_version_of_cmake_counts(tmp_path):
    """Check that a patch release keeps the hash and a minor one changes it."""
    base = _read(tmp_path)
    assert _read(tmp_path, _inputs(cmake="3.28.9")) == base
    assert _read(tmp_path, _inputs(cmake="3.29.0")) != base
