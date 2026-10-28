# test_citations.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests finding and rewriting the citations of a document or an entry."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.citations import citing_files, repair_citations, repair_text, rewrite_ids

pytestmark = pytest.mark.medium


def test_rewrite_ids_leaves_a_sibling_s_id_alone():
    """`sushiweb RW-3` is the sibling's; `RW-3` and `the RW-3` are ours."""
    text, count = rewrite_ids("RW-3, the RW-3 and sushiweb RW-3; RW-30", {"RW-3": "RW-9"}, frozenset({"sushiweb"}))
    assert text == "RW-9, the RW-9 and sushiweb RW-3; RW-30"
    assert count == 2


def test_repair_text_moves_a_path_a_link_and_a_literal(tmp_path: Path):
    """Each kind of citation of a moved file is rewritten."""
    root = tmp_path
    (root / "docs" / "design" / "ATMOSPHERE").mkdir(parents=True)
    (root / "docs" / "design" / "ATMOSPHERE" / "CLOUDS.md").write_text("# Clouds\n", encoding="utf-8")
    page = root / "docs" / "guides" / "SKY.md"
    page.parent.mkdir(parents=True)
    text = (
        "See docs/design/CLOUDS/README.md, [clouds](../design/CLOUDS/README.md#march) "
        "and docs/reference/KNOWN_ISSUES.md.\n"
    )
    moves = {
        "docs/design/CLOUDS/README.md": "docs/design/ATMOSPHERE/CLOUDS.md",
        "docs/reference/KNOWN_ISSUES.md": "docs/backlog/README.md",
    }
    fixed, rewrites = repair_text(page, text, root, {}, moves)
    assert fixed == (
        "See docs/design/ATMOSPHERE/CLOUDS.md, [clouds](../design/ATMOSPHERE/CLOUDS.md#march) "
        "and docs/backlog/README.md.\n"
    )
    assert len(rewrites) == 3


def test_repair_text_places_a_gone_document_in_its_topic(tmp_path: Path):
    """A loose document that became a folder is found through the topics."""
    root = tmp_path
    topic = root / "docs" / "design" / "AUDIO" / "README.md"
    topic.parent.mkdir(parents=True)
    topic.write_text("# Audio\n", encoding="utf-8")
    fixed, rewrites = repair_text(root / "README.md", "See docs/design/AUDIO.md.", root, {"AUDIO": topic})
    assert fixed == "See docs/design/AUDIO/README.md."
    assert rewrites[0].new == "docs/design/AUDIO/README.md"


def test_citing_files_skip_the_archive_and_the_shared_tools(tmp_path: Path):
    """Fixtures in the shared tools and the archive are never rewritten."""
    archived = "/".join(("docs", "archive", "b.md"))
    for relative in ("docs/a.md", archived, "tools/documentation/c.py", "src/d.cpp", "e.bin"):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x", encoding="utf-8")
    found = sorted(path.relative_to(tmp_path).as_posix() for path in citing_files(tmp_path))
    assert found == ["docs/a.md", "src/d.cpp"]


def test_repair_citations_writes_only_with_apply(tmp_path: Path):
    """Without apply nothing changes on disk."""
    page = tmp_path / "README.md"
    page.write_text("See docs/reference/KNOWN_ISSUES.md.\n", encoding="utf-8")
    moves = {"docs/reference/KNOWN_ISSUES.md": "docs/backlog/README.md"}
    assert len(repair_citations(tmp_path, {}, moves, apply=False)) == 1
    assert "KNOWN_ISSUES" in page.read_text(encoding="utf-8")
    repair_citations(tmp_path, {}, moves, apply=True)
    assert page.read_text(encoding="utf-8") == "See docs/backlog/README.md.\n"
