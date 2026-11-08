# test_module_manifest.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the module manifest's dependency fragment."""

import pytest

from sushicore.provision.closure import DEFAULT_FRAGMENT
from sushicore.provision.module_manifest import fragment_from, fragment_path


@pytest.mark.small
def test_a_manifest_that_names_a_fragment_decides_it():
    """Check that the manifest's fragment key decides the fragment."""
    manifest = {"module": {"name": "x", "fragment": "tooling/x.deps.toml"}}
    assert fragment_from(manifest) == "tooling/x.deps.toml"


@pytest.mark.small
def test_a_manifest_without_the_key_leaves_the_default():
    """Check that a manifest without the fragment key gives the default."""
    assert fragment_from({"module": {"name": "x"}}) == DEFAULT_FRAGMENT


@pytest.mark.small
def test_an_empty_manifest_leaves_the_default():
    """Check that a manifest with no content gives the default."""
    assert fragment_from({}) == DEFAULT_FRAGMENT


@pytest.mark.small
@pytest.mark.parametrize("value", [3, "", "   ", None])
def test_a_value_that_is_no_path_leaves_the_default(value):
    """Check that a value that is not a non-blank string gives the default."""
    assert fragment_from({"module": {"fragment": value}}) == DEFAULT_FRAGMENT


@pytest.mark.medium
def test_a_module_folder_without_a_manifest_leaves_the_default(tmp_path):
    """Check that a folder holding no manifest gives the default."""
    assert fragment_path(tmp_path) == DEFAULT_FRAGMENT


@pytest.mark.medium
def test_a_manifest_file_is_read_for_its_fragment(tmp_path):
    """Check that the manifest file of a module folder is read."""
    (tmp_path / "sushi-module.toml").write_text(
        '[module]\nfragment = "tooling/x.deps.toml"\n', encoding="utf-8")
    assert fragment_path(tmp_path) == "tooling/x.deps.toml"
