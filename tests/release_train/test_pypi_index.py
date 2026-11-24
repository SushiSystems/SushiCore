# test_pypi_index.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for waiting on a version of a package on PyPI."""

import pytest

from sushicore.release_train.pypi_index import K_MAX_POLLS, PyPiIndex
from sushicore.release_train.version import Version

pytestmark = pytest.mark.small


def test_the_wait_ends_when_the_version_is_listed():
    answers = [{"releases": {"0.5.1": []}}, {"releases": {"0.5.1": [], "0.5.2": []}}]
    sleeps = []
    assert PyPiIndex(sleeps.append, lambda _package: answers.pop(0)).wait_for("x-cli", Version(0, 5, 2))
    assert len(sleeps) == 1


def test_an_unreadable_index_fails_after_the_last_poll():
    sleeps = []
    assert not PyPiIndex(sleeps.append, lambda _package: {}).wait_for("x-cli", Version(0, 5, 2))
    assert len(sleeps) == K_MAX_POLLS
