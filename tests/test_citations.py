# test_citations.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests finding and rewriting the citations of a document or an entry."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.citations import (Rewrite, citing_files, repair_citations, repair_text,
                                 rewrite_id_citations, rewrite_ids)


def _write_files(root: Path, relatives: tuple[str, ...]) -> None:
    """Write a one-line file at each of the paths *relatives* below *root*."""
    for relative in relatives:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x", encoding="utf-8")


@pytest.mark.small
def test_rewrite_ids_leaves_a_sibling_s_id_alone():
    """`sushiweb RW-3` is the sibling's; `RW-3` and `the RW-3` are ours."""
    text, count = rewrite_ids("RW-3, the RW-3 and sushiweb RW-3; RW-30", {"RW-3": "RW-9"}, frozenset({"sushiweb"}))
    assert text == "RW-9, the RW-9 and sushiweb RW-3; RW-30"
    assert count == 2


@pytest.mark.medium
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


@pytest.mark.medium
def test_repair_text_places_a_gone_document_in_its_topic(tmp_path: Path):
    """A loose document that became a folder is found through the topics."""
    root = tmp_path
    topic = root / "docs" / "design" / "AUDIO" / "README.md"
    topic.parent.mkdir(parents=True)
    topic.write_text("# Audio\n", encoding="utf-8")
    fixed, rewrites = repair_text(root / "README.md", "See docs/design/AUDIO.md.", root, {"AUDIO": topic})
    assert fixed == "See docs/design/AUDIO/README.md."
    assert rewrites[0].new == "docs/design/AUDIO/README.md"


@pytest.mark.medium
def test_citing_files_skip_the_archive_and_the_shared_tools(tmp_path: Path):
    """Fixtures in the shared tools and the archive are never rewritten."""
    archived = "/".join(("docs", "archive", "b.md"))
    _write_files(tmp_path, ("docs/a.md", archived, "tools/documentation/c.py", "src/d.cpp", "e.bin"))
    found = sorted(path.relative_to(tmp_path).as_posix() for path in citing_files(tmp_path))
    assert found == ["docs/a.md", "src/d.cpp"]


@pytest.mark.medium
def test_repair_citations_writes_only_with_apply(tmp_path: Path):
    """Without apply nothing changes on disk."""
    page = tmp_path / "README.md"
    page.write_text("See docs/reference/KNOWN_ISSUES.md.\n", encoding="utf-8")
    moves = {"docs/reference/KNOWN_ISSUES.md": "docs/backlog/README.md"}
    assert len(repair_citations(tmp_path, {}, moves, apply=False)) == 1
    assert "KNOWN_ISSUES" in page.read_text(encoding="utf-8")
    repair_citations(tmp_path, {}, moves, apply=True)
    assert page.read_text(encoding="utf-8") == "See docs/backlog/README.md.\n"


@pytest.mark.medium
def test_rewrite_id_citations_lists_every_citation_of_a_renamed_id_without_apply(tmp_path: Path):
    """Without apply the citations are listed and the file is left as it was."""
    page = tmp_path / "a.md"
    page.write_text("see RW-3 and RW-30\nnothing here\nRW-3 again\n", encoding="utf-8")
    found = rewrite_id_citations(tmp_path, {"RW-3": "RW-9"}, apply=False)
    assert found == [Rewrite(page, 1, "see RW-3 and RW-30", "see RW-9 and RW-30"),
                     Rewrite(page, 3, "RW-3 again", "RW-9 again")]
    assert page.read_text(encoding="utf-8") == "see RW-3 and RW-30\nnothing here\nRW-3 again\n"


@pytest.mark.medium
def test_rewrite_id_citations_rewrites_every_citation_of_a_renamed_id_with_apply(tmp_path: Path):
    """With apply each citation of the old ID below the root is replaced in its file."""
    page = tmp_path / "a.md"
    page.write_text("see RW-3 and RW-30\nRW-3 again\n", encoding="utf-8")
    rewrite_id_citations(tmp_path, {"RW-3": "RW-9"}, apply=True)
    assert page.read_text(encoding="utf-8") == "see RW-9 and RW-30\nRW-9 again\n"
