# test_bundle_manifest.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Pins the `bundle.json` document, the contract the documentation site reads."""

from __future__ import annotations

from sushicore.docs_bundle.bundle_manifest import BundleIdentity, build_manifest
from sushicore.docs_bundle.page_set import PageCollector
from sushicore.docs_bundle.publish_list import read_publish_list

K_IDENTITY = BundleIdentity(version="1.2.3", commit="c0ffee")

K_GOLDEN = {
    "schema": 1,
    "repository": "sample",
    "title": "Sample",
    "summary": "A sample repository.",
    "version": "1.2.3",
    "commit": "c0ffee",
    "source_url": "https://github.com/SushiSystems/Sample",
    "pages": [
        {
            "path": "pages/guides/BUILDING.md",
            "section": "guides",
            "title": "Building",
            "order": 2,
            "source": "docs/guides/BUILDING.md",
        },
        {
            "path": "pages/guides/FAQ.md",
            "section": "guides",
            "title": "FAQ",
            "order": 3,
            "source": "docs/guides/FAQ.md",
        },
        {
            "path": "pages/architecture/OVERVIEW.md",
            "section": "architecture",
            "title": "Overview",
            "order": 1,
            "source": "docs/architecture/OVERVIEW.md",
        },
    ],
    "assets": ["pages/guides/images/shot.png"],
    "faq": "pages/guides/FAQ.md",
    "api": None,
}


def _manifest(repository, *, has_api: bool) -> dict:
    """Builds the manifest of the sample repository."""
    publish_list = read_publish_list(repository / "docs")
    page_set = PageCollector(repository, publish_list).collect()
    return build_manifest(K_IDENTITY, publish_list, page_set, has_api=has_api)


def test_build_matches_the_golden_document(repository):
    """Produces exactly the document the contract fixes, key order included."""
    manifest = _manifest(repository, has_api=False)
    assert manifest == K_GOLDEN
    assert list(manifest) == list(K_GOLDEN)


def test_build_names_the_api_root_when_the_bundle_carries_one(repository):
    """Records the format and the folder of the API reference."""
    assert _manifest(repository, has_api=True)["api"] == {
        "format": "doxygen-xml",
        "root": "api/xml",
    }
