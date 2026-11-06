# test_page_set.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests that a repository's published pages and their assets are collected and checked."""

from __future__ import annotations

from dataclasses import replace

import pytest

from sushicore.docs_bundle.errors import PageError, PublishListError
from sushicore.docs_bundle.page_set import Page, PageCollector, PageSet
from sushicore.docs_bundle.publish_list import read_publish_list
from sushicore.files_memory import MemoryFiles

from .sample_repository import K_MEMORY_ROOT


pytestmark = pytest.mark.small

K_DOCS = K_MEMORY_ROOT / "docs"
K_SAMPLE_PAGES = (
    Page("guides/BUILDING.md", "guides", "Building", 2),
    Page("guides/FAQ.md", "guides", "FAQ", 3),
    Page("architecture/OVERVIEW.md", "architecture", "Overview", 1),
)


def _collect(files: MemoryFiles, **changes) -> PageSet:
    """Collects the sample's pages, with *changes* applied to its publish list."""
    publish_list = replace(read_publish_list(K_DOCS, files=files), **changes)
    return PageCollector(K_MEMORY_ROOT, publish_list, files=files).collect()


def _put(files: MemoryFiles, relative: str, text: str) -> None:
    """Writes one file below the sample's docs/ folder."""
    files.write_text(K_DOCS / relative, text)


def test_collect_returns_the_pages_in_section_then_index_order(memory_repository):
    """Orders pages by section, then by their position in the index."""
    assert _collect(memory_repository) == PageSet(
        pages=K_SAMPLE_PAGES,
        assets=("guides/images/shot.png",),
        faq="guides/FAQ.md",
    )


def test_collect_leaves_out_an_excluded_page(memory_repository):
    """Publishes neither an excluded page nor an FAQ that was excluded."""
    page_set = _collect(memory_repository, exclude=frozenset({"guides/FAQ.md"}))
    assert [page.source for page in page_set.pages] == [
        "guides/BUILDING.md",
        "architecture/OVERVIEW.md",
    ]
    assert page_set.faq is None


@pytest.mark.parametrize("name", ["guides/FAQ.MD.md", "guides/faq.md"])
def test_collect_refuses_an_exclusion_that_names_no_page(memory_repository, name):
    """Stops on a misspelt or differently cased exclusion, which would publish the page it hid."""
    with pytest.raises(PublishListError) as caught:
        _collect(memory_repository, exclude=frozenset({name}))
    assert f"exclude names {name}, which is not a page of a listed section." in str(caught.value)


def test_collect_reports_a_link_to_a_missing_file(memory_repository):
    """Names the page and the line of a link whose target does not exist."""
    _put(memory_repository, "guides/BUILDING.md", "# Building\n\n\n[gone](NOWHERE.md)\n")
    with pytest.raises(PageError) as caught:
        _collect(memory_repository)
    assert (caught.value.path, caught.value.line) == (K_DOCS / "guides" / "BUILDING.md", 4)
    assert "NOWHERE.md" in str(caught.value)


@pytest.mark.parametrize("target", ["/etc/hosts", "../../../outside.md"])
def test_collect_reports_a_link_that_cannot_be_resolved(memory_repository, target):
    """Refuses an absolute path and a path that leaves the repository."""
    _put(memory_repository, "guides/BUILDING.md", f"# Building\n\n[x]({target})\n")
    with pytest.raises(PageError) as caught:
        _collect(memory_repository)
    assert caught.value.line == 3


def test_collect_reports_a_page_without_a_title(memory_repository):
    """Names a page that has no level-one heading."""
    _put(memory_repository, "guides/BUILDING.md", "## Building\n")
    with pytest.raises(PageError) as caught:
        _collect(memory_repository)
    assert caught.value.path == K_DOCS / "guides" / "BUILDING.md"


def test_collect_reports_a_page_the_index_does_not_link(memory_repository):
    """Names the index and the page when a published page has no order."""
    _put(memory_repository, "guides/ORPHAN.md", "# Orphan\n")
    with pytest.raises(PageError) as caught:
        _collect(memory_repository)
    assert caught.value.path == K_DOCS / "README.md"
    assert "guides/ORPHAN.md" in str(caught.value)


def test_collect_refuses_a_list_that_publishes_nothing(memory_repository):
    """Stops when the listed sections hold no Markdown file."""
    with pytest.raises(PublishListError) as caught:
        _collect(memory_repository, sections=("reference",))
    assert "the listed sections hold no page to publish." in str(caught.value)


@pytest.mark.parametrize("target", [r"..\design\secret.png", "..%5Cdesign%5Csecret.png"])
def test_collect_refuses_a_link_written_with_backslashes(memory_repository, target):
    """Stops on a backslash, which a Windows path would follow into an unlisted folder."""
    _put(memory_repository, "design/secret.png", "x")
    _put(memory_repository, "guides/BUILDING.md", f"# Building\n\n![x]({target})\n")
    with pytest.raises(PageError) as caught:
        _collect(memory_repository)
    assert caught.value.line == 3
    assert "forward slashes" in str(caught.value)


def test_collect_never_carries_an_excluded_page_as_an_asset(memory_repository):
    """Treats `.MD` as a page, so excluding it keeps it out when a page links to it."""
    _put(memory_repository, "guides/HIDDEN.MD", "# Hidden\n")
    _put(memory_repository, "guides/BUILDING.md", "# Building\n\n[h](HIDDEN.MD)\n")
    page_set = _collect(memory_repository, exclude=frozenset({"guides/HIDDEN.MD"}))
    assert page_set == PageSet(pages=K_SAMPLE_PAGES, assets=(), faq="guides/FAQ.md")
