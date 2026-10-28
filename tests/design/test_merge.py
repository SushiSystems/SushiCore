# test_merge.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests `overlap` and `merge`."""

from __future__ import annotations

import pytest

from sushicore.design import DesignError, TopicMerger, check_design, find_overlap

pytestmark = pytest.mark.medium


def _two_topics(store) -> None:
    """Writes ATMOSPHERE and VOLUMETRIC_CLOUDS, which both name the clouds module."""
    store.create("ATMOSPHERE", modules=["modules/atmosphere"], about="The air.")
    store.create("VOLUMETRIC_CLOUDS", modules=["modules/clouds"], about="The clouds.")
    store.add_phase("ATMOSPHERE", "A1", "Scatter light")
    store.add_phase("VOLUMETRIC_CLOUDS", "A1", "March the clouds")
    store.add_phase("VOLUMETRIC_CLOUDS", "C2", "Shadow the clouds")
    clouds = store.topic("VOLUMETRIC_CLOUDS").path
    clouds.write_text(
        clouds.read_text(encoding="utf-8").replace("`modules/clouds`", "`modules/clouds`, `modules/atmosphere`")
        .replace("## Problem\n\nNone.", "## Problem\n\nThe clouds stretch; see [the march](MARCH.md)."),
        encoding="utf-8",
    )
    (clouds.parent / "MARCH.md").write_text("# March\n", encoding="utf-8")


def test_overlap_lists_shared_and_nested_modules_and_shared_words(store):
    """Each kind of overlap is found."""
    store.create("ATMOSPHERE", modules=["modules/atmosphere"], about="The air.")
    store.create("ATMOSPHERE_SKY", modules=["modules/clouds"], about="The sky.")
    path = store.topic("ATMOSPHERE_SKY").path
    path.write_text(path.read_text(encoding="utf-8").replace("`modules/clouds`", "`modules/clouds`, `modules/atmosphere/sky`"), encoding="utf-8")
    found = find_overlap(store)
    assert found.shared == ()
    assert found.nested == (("modules/atmosphere", "ATMOSPHERE", "modules/atmosphere/sky", "ATMOSPHERE_SKY"),)
    assert found.words == (("ATMOSPHERE", "ATMOSPHERE_SKY", "ATMOSPHERE"),)


def test_merge_makes_a_page_joins_phases_and_modules_and_rewrites_citations(store):
    """After a merge the repository checks clean and every citation points at the page."""
    _two_topics(store)
    work = store.root / "docs" / "agent" / "2026_10_28_CLOUDS" / "SPEC.md"
    work.parent.mkdir(parents=True)
    work.write_text("# Clouds\n\n**Status:** Open — x\n**Implements:** VOLUMETRIC_CLOUDS#A1\n", encoding="utf-8")
    readme = store.root / "README.md"
    readme.write_text("See docs/design/VOLUMETRIC_CLOUDS/README.md and docs/design/VOLUMETRIC_CLOUDS/MARCH.md.\n", encoding="utf-8")
    result = TopicMerger(store).merge("ATMOSPHERE", "VOLUMETRIC_CLOUDS")
    assert result.renamed_phases == (("A1", "VOLUMETRIC_CLOUDS-A1"),)
    assert not (store.design / "VOLUMETRIC_CLOUDS").exists()
    page = (store.design / "ATMOSPHERE" / "VOLUMETRIC_CLOUDS.md").read_text(encoding="utf-8")
    assert "The clouds stretch" in page and "**Status:**" not in page and "| Id |" not in page
    topic = store.topic("ATMOSPHERE").document
    assert [p.ident for p in topic.phases] == ["A1", "VOLUMETRIC_CLOUDS-A1", "C2"]
    assert topic.modules() == ["modules/atmosphere", "modules/clouds"]
    assert "ATMOSPHERE#VOLUMETRIC_CLOUDS-A1" in work.read_text(encoding="utf-8")
    assert readme.read_text(encoding="utf-8") == (
        "See docs/design/ATMOSPHERE/VOLUMETRIC_CLOUDS.md and docs/design/ATMOSPHERE/MARCH.md.\n")
    assert check_design(store) == []


def test_merge_refuses_itself_and_a_page_that_exists(store):
    """A topic is not merged into itself, nor over a page."""
    _two_topics(store)
    with pytest.raises(DesignError):
        TopicMerger(store).merge("ATMOSPHERE", "ATMOSPHERE")
    (store.design / "ATMOSPHERE" / "VOLUMETRIC_CLOUDS.md").write_text("# x\n", encoding="utf-8")
    with pytest.raises(DesignError):
        TopicMerger(store).merge("ATMOSPHERE", "VOLUMETRIC_CLOUDS")


def test_merge_renames_a_page_whose_name_is_taken(store):
    """A page of the merged topic that clashes gets its topic's name in front."""
    _two_topics(store)
    (store.design / "ATMOSPHERE" / "MARCH.md").write_text("# Mine\n", encoding="utf-8")
    TopicMerger(store).merge("ATMOSPHERE", "VOLUMETRIC_CLOUDS")
    assert (store.design / "ATMOSPHERE" / "VOLUMETRIC_CLOUDS_MARCH.md").is_file()
    page = (store.design / "ATMOSPHERE" / "VOLUMETRIC_CLOUDS.md").read_text(encoding="utf-8")
    assert "](VOLUMETRIC_CLOUDS_MARCH.md)" in page
