# test_module_manifest.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests reading the dependency fragment a module declares in its manifest."""

import pytest

from sushicore.provision.closure import DEFAULT_FRAGMENT
from sushicore.provision.module_manifest import fragment_path


pytestmark = pytest.mark.small


def test_a_manifest_that_names_a_fragment_decides_it(tmp_path):
    (tmp_path / "sushi-module.toml").write_text('[module]\nname = "x"\nfragment = "tooling/x.deps.toml"\n', encoding="utf-8")
    assert fragment_path(tmp_path) == "tooling/x.deps.toml"


def test_a_manifest_without_the_key_leaves_the_default(tmp_path):
    (tmp_path / "sushi-module.toml").write_text('[module]\nname = "x"\n', encoding="utf-8")
    assert fragment_path(tmp_path) == DEFAULT_FRAGMENT


def test_no_manifest_leaves_the_default(tmp_path):
    assert fragment_path(tmp_path) == DEFAULT_FRAGMENT


@pytest.mark.parametrize("value", ["3", "''", "'   '"])
def test_a_value_that_is_no_path_leaves_the_default(tmp_path, value):
    (tmp_path / "sushi-module.toml").write_text(f"[module]\nfragment = {value}\n", encoding="utf-8")
    assert fragment_path(tmp_path) == DEFAULT_FRAGMENT
