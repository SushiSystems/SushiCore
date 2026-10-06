# test_packages_base.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""A PATH refresh the registry refuses is recorded and a defect in it escapes."""

from __future__ import annotations

import os
import sys
import types

import pytest

from sushicore.provision.packages import base

pytestmark = pytest.mark.skipif(os.name != "nt", reason="the PATH refresh reads the registry")


def _winreg_raising(monkeypatch, error: Exception) -> None:
    """Install a ``winreg`` whose ``OpenKey`` raises *error*."""
    def open_key(*_args):
        """Raise the configured error in place of opening the key."""
        raise error

    fake = types.SimpleNamespace(HKEY_LOCAL_MACHINE=1, HKEY_CURRENT_USER=2, OpenKey=open_key)
    monkeypatch.setitem(sys.modules, "winreg", fake)


def test_a_refused_registry_read_is_recorded_and_leaves_path_alone(monkeypatch, caplog):
    """Check that a registry the process may not read yields one warning and the old PATH."""
    _winreg_raising(monkeypatch, PermissionError(5, "Access is denied"))
    monkeypatch.setenv("PATH", "C:/base")
    with caplog.at_level("WARNING", logger="sushicore.provision"):
        base.refresh_windows_path()
    warnings = [r.getMessage() for r in caplog.records
                if r.name == "sushicore.provision" and r.levelname == "WARNING"]
    assert len(warnings) == 1
    assert "Access is denied" in warnings[0]
    assert os.environ["PATH"] == "C:/base"


def test_a_defect_in_the_registry_read_is_not_swallowed(monkeypatch):
    """Check that an error the registry does not raise escapes the refresh."""
    _winreg_raising(monkeypatch, TypeError("defect"))
    with pytest.raises(TypeError):
        base.refresh_windows_path()
