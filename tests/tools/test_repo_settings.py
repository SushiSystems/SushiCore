# test_repo_settings.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for finding the settings of the repository being checked."""

import pytest

from sushicore.tools.repo_settings import K_ROOT_VARIABLE, K_SETTINGS, settings_path

pytestmark = pytest.mark.medium


def _repository(folder):
    (folder / K_SETTINGS).parent.mkdir(parents=True)
    (folder / K_SETTINGS).write_text("K_X = 1\n", encoding="utf-8")
    return folder / K_SETTINGS


def test_the_nearest_settings_at_or_above_the_start_are_found(tmp_path):
    found = _repository(tmp_path)
    inner = tmp_path / "docs" / "guides"
    inner.mkdir(parents=True)
    assert settings_path(inner, {}) == found


def test_the_variable_names_the_repository_over_the_start(tmp_path):
    named = _repository(tmp_path / "named")
    _repository(tmp_path / "start")
    assert settings_path(tmp_path / "start", {K_ROOT_VARIABLE: str(tmp_path / "named")}) == named


def test_no_settings_raise_naming_where_it_looked(tmp_path):
    with pytest.raises(ImportError, match="no tools/settings.py"):
        settings_path(tmp_path, {K_ROOT_VARIABLE: str(tmp_path)})
