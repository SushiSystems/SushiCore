# page_set.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Collects the pages and assets a repository publishes and checks every link they hold.

A link may leave the bundle; `docs/reference/DOCS_BUNDLE.md` says what the site does with
it. A link whose target does not exist stops the collection.
"""

from __future__ import annotations

import posixpath
from dataclasses import dataclass
from pathlib import Path
from typing import final

from .errors import PageError, PublishListError
from .markdown_scan import MarkdownLink, first_heading, iter_links, local_path
from .page_order import K_INDEX_NAME, read_page_order
from .page_text import is_page, read_page_text
from .publish_list import K_FILE_NAME, K_SECTIONS, PublishList

K_DOCS = "docs"
K_FAQ = "guides/FAQ.md"
K_BACKSLASH = "\\"


@dataclass(frozen=True, slots=True)
class Page:
    """Holds one published page: its path below docs/, section, title and order."""

    source: str
    section: str
    title: str
    order: int


@dataclass(frozen=True, slots=True)
class PageSet:
    """Holds everything a bundle carries under pages/."""

    pages: tuple[Page, ...]
    assets: tuple[str, ...]
    faq: str | None


@final
class PageCollector:
    """Collects the published pages of one repository."""

    def __init__(self, repository_root: Path, publish_list: PublishList) -> None:
        """Stores the repository and the list that says what it publishes."""
        self._root = repository_root
        self._docs = repository_root / K_DOCS
        self._publish_list = publish_list

    def collect(self) -> PageSet:
        """Returns the published pages in section and index order, with their assets.

        Raises:
            PublishListError: An exclusion names no page, or nothing is published.
            PageError: A page has no title, no order, or a link to a missing file.
        """
        sources = self._published_sources()
        order = read_page_order(self._docs)
        known = frozenset(sources)
        pages: list[Page] = []
        assets: set[str] = set()
        for source in sources:
            path = self._docs / source
            text = read_page_text(path)
            title = first_heading(text)
            if title is None:
                raise PageError(path, 1, "has no level-one heading to take its title from")
            if source not in order:
                raise PageError(
                    self._docs / K_INDEX_NAME, 1,
                    f"does not reach {source} through its links, so the page has no order",
                )
            for link in iter_links(text):
                asset = self._asset_of(path, source, link, known)
                if asset is not None:
                    assets.add(asset)
            pages.append(Page(source, source.split("/", 1)[0], title, order[source]))
        pages.sort(key=lambda page: (K_SECTIONS.index(page.section), page.order))
        return PageSet(tuple(pages), tuple(sorted(assets)), K_FAQ if K_FAQ in known else None)

    def _published_sources(self) -> list[str]:
        """Returns the path below docs/ of every page in a listed section, less the exclusions."""
        list_path = self._docs / K_FILE_NAME
        found: list[str] = []
        for section in self._publish_list.sections:
            for path in sorted((self._docs / section).rglob("*")):
                if path.is_file() and is_page(path.name):
                    found.append(path.relative_to(self._docs).as_posix())
        unknown = sorted(self._publish_list.exclude - set(found))
        if unknown:
            raise PublishListError(
                f"{list_path}: exclude names {unknown[0]}, which is not a page of a listed section."
            )
        sources = [source for source in found if source not in self._publish_list.exclude]
        if not sources:
            raise PublishListError(f"{list_path}: the listed sections hold no page to publish.")
        return sources

    def _asset_of(
        self, path: Path, source: str, link: MarkdownLink, known: frozenset[str],
    ) -> str | None:
        """Returns the asset a link names, or None for a page or a file outside the bundle."""
        local = local_path(link.target)
        if local is None:
            return None
        if K_BACKSLASH in local:
            raise PageError(
                path, link.line,
                f"links to {link.target} with a backslash; write the path with forward slashes",
            )
        if local.startswith("/"):
            raise PageError(path, link.line, f"links to {link.target}, an absolute path")
        target = posixpath.normpath(posixpath.join(K_DOCS, posixpath.dirname(source), local))
        if target.startswith(".."):
            raise PageError(path, link.line, f"links to {link.target}, which leaves the repository")
        if not (self._root / target).exists():
            raise PageError(path, link.line, f"links to {link.target}, which does not exist")
        if not target.startswith(K_DOCS + "/"):
            return None
        inside = target[len(K_DOCS) + 1:]
        if inside in known or is_page(inside):
            return None
        published = inside.split("/", 1)[0] in self._publish_list.sections
        return inside if published and (self._root / target).is_file() else None
