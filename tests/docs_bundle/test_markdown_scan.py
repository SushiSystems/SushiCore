# test_markdown_scan.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests what the Markdown scan reads out of a page: its links and its title."""

from __future__ import annotations

from sushicore.docs_bundle.markdown_scan import (
    MarkdownLink,
    first_heading,
    iter_links,
    local_path,
)


def test_iter_links_reports_each_target_with_its_line():
    """Reads inline links and images, with the line each stands on."""
    text = "# T\n\nSee [a](one.md) and ![b](two.png).\n[c](three.md#part)\n"
    assert list(iter_links(text)) == [
        MarkdownLink("one.md", 3),
        MarkdownLink("two.png", 3),
        MarkdownLink("three.md#part", 4),
    ]


def test_iter_links_reads_titled_and_bracketed_targets():
    """Finds the target when a title follows it or angle brackets wrap it."""
    text = '[a](one.md "The title")\n[b](<two.md>)\n[`c`](three.md)\n'
    assert [link.target for link in iter_links(text)] == ["one.md", "two.md", "three.md"]


def test_iter_links_skips_code():
    """Ignores a link written inside a fenced block or a code span."""
    text = "```\n[a](fenced.md)\n```\nUse `[b](span.md)` here.\n~~~\n[c](tilde.md)\n~~~\n"
    assert list(iter_links(text)) == []


def test_first_heading_returns_the_first_level_one_heading():
    """Returns the first `# ` heading and skips one inside a fenced block."""
    assert first_heading("```\n# not this\n```\n\n## Nor this\n\n# The title #\n") == "The title"
    assert first_heading("## Only a second level\n") is None


def test_local_path_drops_the_fragment_and_refuses_addresses():
    """Returns the file part of a target and None for an address or a bare anchor."""
    assert local_path("guides/A%20B.md#part") == "guides/A B.md"
    assert local_path("page.md?raw=1") == "page.md"
    assert local_path("https://sushisystems.io") is None
    assert local_path("mailto:a@b.io") is None
    assert local_path("#part") is None
    assert local_path("//cdn.example/x.png") is None
