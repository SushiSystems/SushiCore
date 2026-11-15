# test_header_merger.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the license header rules a shared file is put under."""

from __future__ import annotations

import pytest

from sushicore.shared_tools.header_merger import first_year, split_header

pytestmark = pytest.mark.small


def test_split_header_cuts_the_leading_comment_run():
    """The header is the comment lines before the first other line."""
    assert split_header("# a\n# b\nx = 1\n# c\n") == ("# a\n# b\n", "x = 1\n# c\n")


def test_first_year_reads_the_first_copyright_row_it_finds():
    """The first text holding a row decides; none gives this year."""
    assert first_year(2030, None, "# Copyright (c) 2024-present A", "# Copyright (c) 2020-present A") == 2024
    assert first_year(2030, "no row") == 2030
