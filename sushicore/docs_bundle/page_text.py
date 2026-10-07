# page_text.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Reads the text of a Markdown page and decides which files are pages."""

from __future__ import annotations

from pathlib import Path

from .errors import PageError

K_PAGE_SUFFIX = ".md"
K_ENCODING = "utf-8-sig"


def is_page(name: str) -> bool:
    """Returns whether a file name is a Markdown page, whatever the case of its suffix."""
    return name.lower().endswith(K_PAGE_SUFFIX)


def read_page_text(path: Path) -> str:
    """Returns a page's text, decoded as UTF-8 and without a byte order mark.

    Raises:
        PageError: The file's bytes are not UTF-8.
    """
    try:
        return path.read_text(encoding=K_ENCODING)
    except UnicodeDecodeError as error:
        raise PageError(path, 1, f"is not UTF-8 text: {error.reason}") from error
