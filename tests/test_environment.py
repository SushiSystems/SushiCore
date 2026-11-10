# test_environment.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What the process environment promises: the Environment port over ``os.environ``."""

from __future__ import annotations

import pytest

from sushicore.environment import ProcessEnvironment

pytestmark = pytest.mark.small


def test_the_process_environment_reads_os_environ_live(monkeypatch):
    environment = ProcessEnvironment()
    monkeypatch.setenv("SUSHICORE_TEST_ONLY", "x")
    assert environment.has("SUSHICORE_TEST_ONLY") and environment.get("SUSHICORE_TEST_ONLY") == "x"
    monkeypatch.delenv("SUSHICORE_TEST_ONLY")
    assert environment.get("SUSHICORE_TEST_ONLY", "gone") == "gone"
