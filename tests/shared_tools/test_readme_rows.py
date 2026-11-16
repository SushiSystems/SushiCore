# test_readme_rows.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the merge of the shared rows into a repository's tools README."""

from __future__ import annotations

import pytest

from sushicore.shared_tools.readme_rows import merge_readme

pytestmark = pytest.mark.small

K_HEAD = "| Path | Checks | Takes |\n| --- | --- | --- |\n"
K_SOURCE = (
    "# tools\n\n" + K_HEAD
    + "| `a.py` | New A | Root |\n| `settings.py` | Settings | |\n| `sub/b.py` | B | Root |\n| `tests/` | Unit tests | |\n"
)
K_SHARED = ["tools/a.py", "tools/sub/b.py", "tools/tests/test_a.py"]


def test_a_shared_row_is_added_after_the_last_own_row() -> None:
    """The own row stays first and the shared rows follow it."""
    current = "# own\n\n" + K_HEAD + "| `own.py` | Mine | Root |\n\nAfter.\n"
    lines = merge_readme(current, K_SOURCE, K_SHARED).split("\n")
    assert lines[4:8] == ["| `own.py` | Mine | Root |", "| `a.py` | New A | Root |", "| `sub/b.py` | B | Root |", "| `tests/` | Unit tests | |"]
    assert "After." in lines


def test_a_row_of_an_excluded_path_is_not_written() -> None:
    """A row whose file is not shared stays out of the README."""
    assert "settings.py" not in merge_readme(None, K_SOURCE, K_SHARED)


def test_a_shared_row_replaces_the_row_the_repository_holds() -> None:
    """The row of a shared tool takes the text of the source and is not repeated."""
    current = K_HEAD + "| `a.py` | Old A | Root |\n| `own.py` | Mine | Root |\n"
    merged = merge_readme(current, K_SOURCE, K_SHARED)
    assert merged.count("| `a.py` |") == 1
    assert "| `a.py` | New A | Root |" in merged
    assert "| `own.py` | Mine | Root |" in merged


def test_a_readme_without_a_table_gets_the_table_after_its_text() -> None:
    """The text the repository wrote stays and the table follows."""
    merged = merge_readme("own readme\n", K_SOURCE, K_SHARED)
    assert merged.startswith("own readme\n\n| Path | Checks | Takes |")
    assert "| `a.py` | New A | Root |" in merged


def test_a_second_merge_changes_nothing() -> None:
    """Merging into a merged README gives the same text."""
    once = merge_readme(None, K_SOURCE, K_SHARED)
    assert merge_readme(once, K_SOURCE, K_SHARED) == once
