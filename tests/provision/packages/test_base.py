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


def _refresh_failing_with(error: Exception, caplog) -> tuple[type | None, int, str]:
    """Refresh with a registry that raises *error*; return what escaped, the warnings and the PATH."""
    environ = {"PATH": "C:/base"}
    escaped = None
    with caplog.at_level("WARNING", logger="sushicore.provision"):
        try:
            base.refresh_windows_path(_raising(error), environ)
        except Exception as raised:
            escaped = type(raised)
    warnings = [r for r in caplog.records
                if r.name.startswith("sushicore.provision") and r.levelname == "WARNING"]
    return escaped, len(warnings), environ["PATH"]


@pytest.mark.small
@pytest.mark.parametrize(("error", "escaped", "warnings"), [
    (PermissionError(5, "Access is denied"), None, 1),
    (TypeError("defect"), TypeError, 0),
])
def test_only_a_refused_registry_read_is_recorded_and_a_defect_escapes(
        error, escaped, warnings, caplog):
    """Check that a refused registry read is one warning with the old PATH, and a defect escapes."""
    assert _refresh_failing_with(error, caplog) == (escaped, warnings, "C:/base")


@pytest.mark.small
def test_the_machine_and_user_paths_join_the_old_one_with_the_first_spelling_kept():
    """Check that machine, user and process paths merge in order and a repeat in other case is dropped."""
    environ = {"PATH": os.pathsep.join(["C:/Tools", "C:/old"])}
    base.refresh_windows_path(_reading("C:/tools", "C:/user"), environ)
    assert environ["PATH"] == os.pathsep.join(["C:/tools", "C:/user", "C:/Tools", "C:/old"][:2]
                                              + ["C:/old"])
