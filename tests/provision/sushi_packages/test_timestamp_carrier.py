# test_timestamp_carrier.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the carrying of file times between two install prefixes."""

from __future__ import annotations

import os

import pytest

from sushicore.provision.sushi_packages.timestamp_carrier import TimestampCarrier

pytestmark = pytest.mark.small

K_LONG_AGO = 1_000_000_000


def _write(root, relative, text):
    """Write *text* to *relative* under *root* and return the path."""
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_an_identical_file_takes_the_time_of_the_old_one(tmp_path):
    """Check that equal bytes give the staged file the earlier file's time."""
    old = _write(tmp_path / "old", "include/a.hpp", "same")
    os.utime(old, (K_LONG_AGO, K_LONG_AGO))
    new = _write(tmp_path / "new", "include/a.hpp", "same")
    assert TimestampCarrier().carry(tmp_path / "old", tmp_path / "new") == 1
    assert new.stat().st_mtime == K_LONG_AGO


def test_a_changed_file_keeps_its_own_time(tmp_path):
    """Check that a file with other bytes, of the same size or not, is left alone."""
    for text in ("diff", "longer text"):
        old = _write(tmp_path / "old", "a.hpp", "same")
        os.utime(old, (K_LONG_AGO, K_LONG_AGO))
        new = _write(tmp_path / "new", "a.hpp", text)
        assert TimestampCarrier().carry(tmp_path / "old", tmp_path / "new") == 0
        assert new.stat().st_mtime > K_LONG_AGO


def test_a_file_the_old_prefix_lacks_keeps_its_own_time(tmp_path):
    """Check that a new file and a missing old prefix are not errors."""
    (tmp_path / "old").mkdir()
    new = _write(tmp_path / "new", "b.hpp", "x")
    assert TimestampCarrier().carry(tmp_path / "old", tmp_path / "new") == 0
    assert new.stat().st_mtime > K_LONG_AGO
