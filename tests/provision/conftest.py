# conftest.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Fixtures shared by the provision tests."""

from __future__ import annotations

import pytest

from sushicore import provision
from sushicore.console_memory import RecordingConsole


@pytest.fixture
def recording_console():
    """Bind a recording console for the test, then unbind it."""
    fake = RecordingConsole()
    provision.bind_console(lambda: fake)
    yield fake
    provision.bind_console(None)
