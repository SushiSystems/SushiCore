# test_page_text.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests the reading of a page's text: its encoding and its byte order mark."""

from __future__ import annotations

import pytest

from sushicore.docs_bundle.errors import PageError
from sushicore.docs_bundle.markdown_scan import first_heading
from sushicore.docs_bundle.page_text import read_page_text


def test_read_drops_a_byte_order_mark(tmp_path):
    """Returns the text without the mark, so the first heading is still found."""
    page = tmp_path / "A.md"
    page.write_bytes(b"\xef\xbb\xbf# Title\n")
    assert first_heading(read_page_text(page)) == "Title"


def test_read_reports_a_page_that_is_not_utf_8(tmp_path):
    """Names the file when its bytes are not UTF-8, in place of a decoder traceback."""
    page = tmp_path / "A.md"
    page.write_bytes(b"# Caf\xe9 \xe5\n")
    with pytest.raises(PageError) as caught:
        read_page_text(page)
    assert caught.value.path == page
    assert "UTF-8" in str(caught.value)
