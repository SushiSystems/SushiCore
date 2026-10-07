# bundle_manifest.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Builds `bundle.json`, the one document the site reads about a repository.

The fields and their rules are in `docs/reference/DOCS_BUNDLE.md`.
"""

from __future__ import annotations

from dataclasses import dataclass

from .page_set import K_DOCS, PageSet
from .publish_list import PublishList

K_SCHEMA_VERSION = 1
K_PAGES_DIR = "pages"
K_API_ROOT = "api/xml"
K_API_FORMAT = "doxygen-xml"


@dataclass(frozen=True, slots=True)
class BundleIdentity:
    """Holds the release a bundle is named after and the commit it was built from."""

    version: str
    commit: str


def build_manifest(
    identity: BundleIdentity, publish_list: PublishList, page_set: PageSet, *, has_api: bool,
) -> dict[str, object]:
    """Returns the `bundle.json` document, its keys in the order the contract lists them."""
    return {
        "schema": K_SCHEMA_VERSION,
        "repository": publish_list.name,
        "title": publish_list.title,
        "summary": publish_list.summary,
        "version": identity.version,
        "commit": identity.commit,
        "source_url": publish_list.source_url,
        "pages": [
            {
                "path": f"{K_PAGES_DIR}/{page.source}",
                "section": page.section,
                "title": page.title,
                "order": page.order,
                "source": f"{K_DOCS}/{page.source}",
            }
            for page in page_set.pages
        ],
        "assets": [f"{K_PAGES_DIR}/{asset}" for asset in page_set.assets],
        "faq": None if page_set.faq is None else f"{K_PAGES_DIR}/{page_set.faq}",
        "api": {"format": K_API_FORMAT, "root": K_API_ROOT} if has_api else None,
    }
