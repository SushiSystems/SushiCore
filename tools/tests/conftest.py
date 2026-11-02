# conftest.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Gives the checker tests a size when pytest runs them.

The checker tests are unittest classes copied from SushiSkills, so no file here can carry a mark that a
copy would keep. This file sizes them by what they use: a test file that starts a process or writes a
file is ``medium``, and every other is ``small``. ``unittest discover`` ignores this file.
"""

from __future__ import annotations

import pytest

#: Words in a test file that mean its tests start a process or write a file.
K_MEDIUM_WORDS = ("repo_builder", "subprocess", "tempfile", "TemporaryDirectory", "tmp_path")

K_SIZE_TIMEOUTS = {"small": 60, "medium": 300}


def _size_of(item: pytest.Item) -> str:
    """Returns the size of the test file *item* lives in."""
    text = item.path.read_text(encoding="utf-8")
    return "medium" if any(word in text for word in K_MEDIUM_WORDS) else "small"


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Mark each checker test with its size and the timeout of that size."""
    for item in items:
        size = _size_of(item)
        item.add_marker(getattr(pytest.mark, size))
        item.add_marker(pytest.mark.timeout(K_SIZE_TIMEOUTS[size]))
