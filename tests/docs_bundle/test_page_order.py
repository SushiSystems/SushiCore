# test_page_order.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests the order a page takes from the links of `docs/README.md`."""

from __future__ import annotations

import pytest

from sushicore.docs_bundle.errors import PageError
from sushicore.docs_bundle.page_order import read_page_order

from .sample_repository import write_file


def test_read_numbers_the_pages_in_link_order(repository):
    """Numbers each linked page from 1 in the order the index links to it."""
    assert read_page_order(repository / "docs") == {
        "architecture/OVERVIEW.md": 1,
        "guides/BUILDING.md": 2,
        "guides/FAQ.md": 3,
        "design/SECRET.md": 4,
    }


def test_read_keeps_the_first_position_of_a_repeated_page(repository):
    """Keeps a page's first position when it is linked again or with a fragment."""
    write_file(
        repository,
        "docs/README.md",
        "[A](guides/A.md)\n[B](guides/B.md#part)\n[A again](./guides/A.md)\n[C](guides/C.md)\n",
    )
    assert read_page_order(repository / "docs") == {
        "guides/A.md": 1,
        "guides/B.md": 2,
        "guides/C.md": 3,
    }


def test_read_skips_what_is_not_a_page_below_docs(repository):
    """Skips an address, a file outside docs/ and a file that is not Markdown."""
    write_file(
        repository,
        "docs/README.md",
        "[site](https://sushisystems.io)\n[root](../README.md)\n"
        "[shot](guides/images/shot.png)\n[A](guides/A.md)\n",
    )
    assert read_page_order(repository / "docs") == {"guides/A.md": 1}


def test_read_reports_a_missing_index(tmp_path):
    """Names the index when the documentation tree has none."""
    with pytest.raises(PageError) as caught:
        read_page_order(tmp_path)
    assert "README.md" in str(caught.value)


def test_read_follows_links_through_the_pages_of_the_manual(repository):
    """Orders a page that only another manual page links to, after the pages before it."""
    write_file(repository, "docs/README.md", "[Guide](guides/GUIDE.md)\n[Ref](reference/INDEX.md)\n")
    write_file(repository, "docs/guides/GUIDE.md", "# Guide\n\n[Deep](deep/PART.md)\n")
    write_file(repository, "docs/guides/deep/PART.md", "# Part\n\n[Back](../GUIDE.md)\n")
    write_file(repository, "docs/reference/INDEX.md", "# Index\n\n[One](spice/ONE.md) [Two](spice/TWO.md)\n")
    write_file(repository, "docs/reference/spice/ONE.md", "# One\n")
    write_file(repository, "docs/reference/spice/TWO.md", "# Two\n")
    assert read_page_order(repository / "docs") == {
        "guides/GUIDE.md": 1,
        "reference/INDEX.md": 2,
        "guides/deep/PART.md": 3,
        "reference/spice/ONE.md": 4,
        "reference/spice/TWO.md": 5,
    }


def test_read_does_not_follow_links_out_of_a_page_that_is_not_manual(repository):
    """Gives a design document an order and reads no further through it."""
    write_file(repository, "docs/README.md", "[Design](design/TOPIC.md)\n")
    write_file(repository, "docs/design/TOPIC.md", "# Topic\n\n[Hidden](../guides/HIDDEN.md)\n")
    write_file(repository, "docs/guides/HIDDEN.md", "# Hidden\n")
    assert read_page_order(repository / "docs") == {"design/TOPIC.md": 1}
