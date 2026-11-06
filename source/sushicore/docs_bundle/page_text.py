# page_text.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Reads the text of a Markdown page and decides which files are pages."""

from __future__ import annotations

from pathlib import Path

from ..files import DiskFiles, Files
from .errors import PageError

K_PAGE_SUFFIX = ".md"


def is_page(name: str) -> bool:
    """Returns whether a file name is a Markdown page, whatever the case of its suffix."""
    return name.lower().endswith(K_PAGE_SUFFIX)


def read_page_text(path: Path, *, files: Files | None = None) -> str:
    """Returns a page's text, decoded as UTF-8 and without a byte order mark.

    Args:
        path: The page to read.
        files: The file system the page is read through; the disk when None.

    Raises:
        PageError: The file's bytes are not UTF-8.
    """
    try:
        return (files if files is not None else DiskFiles()).read_text(path)
    except UnicodeDecodeError as error:
        raise PageError(path, 1, f"is not UTF-8 text: {error.reason}") from error
