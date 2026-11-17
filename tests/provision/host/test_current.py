# test_current.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the choice between the hosts."""

from __future__ import annotations

import pytest

from sushicore.provision.host import PosixHost, WindowsHost, current_host
from sushicore.provision.host import current as current_module


@pytest.mark.small
@pytest.mark.parametrize(("name", "expected"), [("nt", WindowsHost), ("posix", PosixHost)])
def test_current_host_follows_the_operating_system_name(monkeypatch, name, expected):
    """Check that the one selection point answers the host of the operating system's name."""
    monkeypatch.setattr(current_module.os, "name", name)

    assert type(current_host()) is expected
