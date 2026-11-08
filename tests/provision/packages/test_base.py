# test_base.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the helpers the package managers share: the PATH refresh."""

from __future__ import annotations

import os

import pytest

from sushicore.provision.packages import base


def _reading(*values):
    """Return a reader that gives the registry Path *values*."""
    return lambda: list(values)


def _raising(error: Exception):
    """Return a reader that raises *error* in place of reading the registry."""
    def read():
        """Raise the configured error."""
        raise error
    return read


@pytest.mark.small
def test_a_refused_registry_read_is_recorded_and_leaves_path_alone(caplog):
    """Check that a registry the process may not read yields one warning and the old PATH."""
    environ = {"PATH": "C:/base"}
    with caplog.at_level("WARNING", logger="sushicore.provision"):
        base.refresh_windows_path(_raising(PermissionError(5, "Access is denied")), environ)
    warnings = [r.getMessage() for r in caplog.records
                if r.name.startswith("sushicore.provision") and r.levelname == "WARNING"]
    assert len(warnings) == 1
    assert "Access is denied" in warnings[0]
    assert environ["PATH"] == "C:/base"


@pytest.mark.small
def test_a_defect_in_the_registry_read_is_not_swallowed():
    """Check that an error the registry does not raise escapes the refresh."""
    with pytest.raises(TypeError):
        base.refresh_windows_path(_raising(TypeError("defect")), {"PATH": ""})


@pytest.mark.small
def test_the_machine_and_user_paths_join_the_old_one_with_the_first_spelling_kept():
    """Check that machine, user and process paths merge in order and a repeat in other case is dropped."""
    environ = {"PATH": os.pathsep.join(["C:/Tools", "C:/old"])}
    base.refresh_windows_path(_reading("C:/tools", "C:/user"), environ)
    assert environ["PATH"] == os.pathsep.join(["C:/tools", "C:/user", "C:/Tools", "C:/old"][:2]
                                              + ["C:/old"])
