# conftest.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Fixtures shared by the provision tests."""

from __future__ import annotations

import pytest

from sushicore.provision._output import bound_memory_console


@pytest.fixture
def recording_console():
    """Bind the in-memory console adapter for the test, then unbind it."""
    with bound_memory_console() as memory:
        yield memory
