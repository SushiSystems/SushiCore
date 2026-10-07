# test_page_set.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests which pages and assets a repository publishes, and which links stop the producer."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from sushicore.docs_bundle.errors import PageError, PublishListError
from sushicore.docs_bundle.page_set import Page, PageCollector, PageSet
from sushicore.docs_bundle.publish_list import read_publish_list

from .sample_repository import write_file


def _collect(repository: Path, **changes) -> PageSet:
    """Collects the sample's pages, with *changes* applied to its publish list."""
    publish_list = replace(read_publish_list(repository / "docs"), **changes)
    return PageCollector(repository, publish_list).collect()


def test_collect_returns_the_pages_in_section_then_index_order(repository):
    """Orders pages by section, then by their position in the index."""
    assert _collect(repository) == PageSet(
        pages=(
            Page("guides/BUILDING.md", "guides", "Building", 2),
            Page("guides/FAQ.md", "guides", "FAQ", 3),
            Page("architecture/OVERVIEW.md", "architecture", "Overview", 1),
        ),
        assets=("guides/images/shot.png",),
        faq="guides/FAQ.md",
    )


def test_collect_leaves_out_an_excluded_page(repository):
    """Publishes neither an excluded page nor an FAQ that was excluded."""
    page_set = _collect(repository, exclude=frozenset({"guides/FAQ.md"}))
    assert [page.source for page in page_set.pages] == [
        "guides/BUILDING.md",
        "architecture/OVERVIEW.md",
    ]
    assert page_set.faq is None


def test_collect_refuses_an_exclusion_that_names_no_file(repository):
    """Stops on a misspelt exclusion, which would publish the page it meant to hide."""
    with pytest.raises(PublishListError) as caught:
        _collect(repository, exclude=frozenset({"guides/FAQ.MD.md"}))
    assert "guides/FAQ.MD.md" in str(caught.value)


def test_collect_refuses_an_exclusion_spelt_in_another_case(repository):
    """Stops on `guides/faq.md`, which a case-blind file system would accept as existing."""
    with pytest.raises(PublishListError):
        _collect(repository, exclude=frozenset({"guides/faq.md"}))


def test_collect_accepts_a_link_that_leaves_the_bundle(repository):
    """Accepts links to a design document and to the root README, and carries neither."""
    page_set = _collect(repository)
    assert all("SECRET" not in page.source for page in page_set.pages)
    assert all("README" not in asset for asset in page_set.assets)


def test_collect_reports_a_link_to_a_missing_file(repository):
    """Names the page and the line of a link whose target does not exist."""
    page = write_file(repository, "docs/guides/BUILDING.md", "# Building\n\n\n[gone](NOWHERE.md)\n")
    with pytest.raises(PageError) as caught:
        _collect(repository)
    assert caught.value.path == page
    assert caught.value.line == 4
    assert "NOWHERE.md" in str(caught.value)


@pytest.mark.parametrize("target", ["/etc/hosts", "../../../outside.md"])
def test_collect_reports_a_link_that_cannot_be_resolved(repository, target):
    """Refuses an absolute path and a path that leaves the repository."""
    write_file(repository, "docs/guides/BUILDING.md", f"# Building\n\n[x]({target})\n")
    with pytest.raises(PageError) as caught:
        _collect(repository)
    assert caught.value.line == 3


def test_collect_reports_a_page_without_a_title(repository):
    """Names a page that has no level-one heading."""
    page = write_file(repository, "docs/guides/BUILDING.md", "## Building\n")
    with pytest.raises(PageError) as caught:
        _collect(repository)
    assert caught.value.path == page


def test_collect_reports_a_page_the_index_does_not_link(repository):
    """Names the index and the page when a published page has no order."""
    write_file(repository, "docs/guides/ORPHAN.md", "# Orphan\n")
    with pytest.raises(PageError) as caught:
        _collect(repository)
    assert caught.value.path == repository / "docs" / "README.md"
    assert "guides/ORPHAN.md" in str(caught.value)


def test_collect_refuses_a_list_that_publishes_nothing(repository):
    """Stops when the listed sections hold no Markdown file."""
    with pytest.raises(PublishListError):
        _collect(repository, sections=("reference",))
