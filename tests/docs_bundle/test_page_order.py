# test_page_order.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests that pages are numbered in the order a walk of links reaches them."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.docs_bundle.errors import PageError
from sushicore.docs_bundle.page_order import read_page_order
from sushicore.files_memory import MemoryFiles

from .sample_repository import K_MEMORY_ROOT


pytestmark = pytest.mark.small

K_DOCS = K_MEMORY_ROOT / "docs"


def _put(files: MemoryFiles, relative: str, text: str) -> None:
    """Writes one page below the sample's docs/ folder."""
    files.write_text(K_DOCS / relative, text)


def test_read_numbers_the_pages_in_link_order(memory_repository):
    """Numbers each linked page from 1 in the order the index links to it."""
    assert read_page_order(K_DOCS, files=memory_repository) == {
        "architecture/OVERVIEW.md": 1,
        "guides/BUILDING.md": 2,
        "guides/FAQ.md": 3,
        "design/SECRET.md": 4,
    }


def test_read_keeps_the_first_position_of_a_repeated_page(memory_repository):
    """Keeps a page's first position when it is linked again or with a fragment."""
    _put(
        memory_repository,
        "README.md",
        "[A](guides/A.md)\n[B](guides/B.md#part)\n[A again](./guides/A.md)\n[C](guides/C.md)\n",
    )
    assert read_page_order(K_DOCS, files=memory_repository) == {
        "guides/A.md": 1,
        "guides/B.md": 2,
        "guides/C.md": 3,
    }


def test_read_skips_what_is_not_a_page_below_docs(memory_repository):
    """Skips an address, a file outside docs/ and a file that is not Markdown."""
    _put(
        memory_repository,
        "README.md",
        "[site](https://sushisystems.io)\n[root](../README.md)\n"
        "[shot](guides/images/shot.png)\n[A](guides/A.md)\n",
    )
    assert read_page_order(K_DOCS, files=memory_repository) == {"guides/A.md": 1}


def test_read_reports_a_missing_index():
    """Names the index when the documentation tree has none."""
    with pytest.raises(PageError) as caught:
        read_page_order(Path("docs"), files=MemoryFiles())
    assert caught.value.path == Path("docs") / "README.md"
    assert "does not exist" in str(caught.value)


def test_read_follows_links_through_the_pages_of_the_manual(memory_repository):
    """Orders a page that only another manual page links to, after the pages before it."""
    _put(memory_repository, "README.md", "[Guide](guides/GUIDE.md)\n[Ref](reference/INDEX.md)\n")
    _put(memory_repository, "guides/GUIDE.md", "# Guide\n\n[Deep](deep/PART.md)\n")
    _put(memory_repository, "guides/deep/PART.md", "# Part\n\n[Back](../GUIDE.md)\n")
    _put(
        memory_repository,
        "reference/INDEX.md",
        "# Index\n\n[One](spice/ONE.md) [Two](spice/TWO.md)\n",
    )
    _put(memory_repository, "reference/spice/ONE.md", "# One\n")
    _put(memory_repository, "reference/spice/TWO.md", "# Two\n")
    assert read_page_order(K_DOCS, files=memory_repository) == {
        "guides/GUIDE.md": 1,
        "reference/INDEX.md": 2,
        "guides/deep/PART.md": 3,
        "reference/spice/ONE.md": 4,
        "reference/spice/TWO.md": 5,
    }


def test_read_follows_links_through_a_document_outside_the_manual(memory_repository):
    """Reaches a page through the contributing page, as the layout checker does."""
    _put(memory_repository, "README.md", "[Contributing](CONTRIBUTING.md)\n")
    _put(memory_repository, "CONTRIBUTING.md", "# Contributing\n\n[Guide](guides/GUIDE.md)\n")
    _put(memory_repository, "guides/GUIDE.md", "# Guide\n")
    assert read_page_order(K_DOCS, files=memory_repository) == {
        "CONTRIBUTING.md": 1,
        "guides/GUIDE.md": 2,
    }


@pytest.mark.parametrize("folder", ["agent", "archive"])
def test_read_does_not_follow_links_out_of_a_record(memory_repository, folder):
    """Gives a work record or an archived document an order and reads no further through it."""
    _put(memory_repository, "README.md", f"[Record]({folder}/RECORD.md)\n")
    _put(memory_repository, f"{folder}/RECORD.md", "# Record\n\n[Hidden](../guides/HIDDEN.md)\n")
    _put(memory_repository, "guides/HIDDEN.md", "# Hidden\n")
    assert read_page_order(K_DOCS, files=memory_repository) == {f"{folder}/RECORD.md": 1}
