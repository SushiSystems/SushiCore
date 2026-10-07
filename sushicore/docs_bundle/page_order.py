# page_order.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Reads the order of the manual's pages by following links from `docs/README.md`.

The walk reads on through every document outside `agent/` and `archive/`, as the reachability
rule of `check_docs_layout.py` does.
"""

from __future__ import annotations

import posixpath
from collections import deque
from pathlib import Path

from .errors import PageError
from .markdown_scan import iter_links, local_path
from .page_text import is_page, read_page_text

K_INDEX_NAME = "README.md"
K_RECORD_FOLDERS = frozenset({"agent", "archive"})


def _is_followed(page: str) -> bool:
    """Returns whether the walk reads on through a page: any but a work record or an archived one."""
    return page.split("/", 1)[0] not in K_RECORD_FOLDERS


def _linked_pages(docs_dir: Path, page: str) -> list[str]:
    """Returns the Markdown files below docs/ a page links to, in reading order."""
    path = docs_dir / page
    if not path.is_file():
        return []
    linked: list[str] = []
    for link in iter_links(read_page_text(path)):
        local = local_path(link.target)
        if local is None:
            continue
        target = posixpath.normpath(posixpath.join(posixpath.dirname(page), local))
        if not target.startswith("..") and is_page(target):
            linked.append(target)
    return linked


def read_page_order(docs_dir: Path) -> dict[str, int]:
    """Returns each page reached from the index, keyed by its path below docs/, with its position.

    Pages are numbered from 1 in the order a breadth-first walk first reaches them: the pages
    the index links to, then the pages those link to. A page under agent/ or archive/ gets a
    position and is not read.

    Raises:
        PageError: The documentation tree has no index.
    """
    if not (docs_dir / K_INDEX_NAME).is_file():
        raise PageError(docs_dir / K_INDEX_NAME, 1, "does not exist; the pages take their order from it")
    order: dict[str, int] = {}
    pending = deque([K_INDEX_NAME])
    while pending:
        for page in _linked_pages(docs_dir, pending.popleft()):
            if page == K_INDEX_NAME or page in order:
                continue
            order[page] = len(order) + 1
            if _is_followed(page):
                pending.append(page)
    return order
