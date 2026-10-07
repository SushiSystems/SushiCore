# page_order.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Reads the order of the manual's pages from the links of `docs/README.md`."""

from __future__ import annotations

import posixpath
from pathlib import Path

from .errors import PageError
from .markdown_scan import iter_links, local_path

K_INDEX_NAME = "README.md"
K_PAGE_SUFFIX = ".md"


def read_page_order(docs_dir: Path) -> dict[str, int]:
    """Returns each page the index links to, keyed by its path below docs/, with its position.

    Raises:
        PageError: The documentation tree has no index.
    """
    index = docs_dir / K_INDEX_NAME
    if not index.is_file():
        raise PageError(index, 1, "does not exist; the pages take their order from it")
    order: dict[str, int] = {}
    for link in iter_links(index.read_text(encoding="utf-8")):
        path = local_path(link.target)
        if path is None:
            continue
        page = posixpath.normpath(path)
        if page.startswith("..") or not page.endswith(K_PAGE_SUFFIX):
            continue
        order.setdefault(page, len(order) + 1)
    return order
