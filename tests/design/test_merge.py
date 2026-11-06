# test_merge.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests `overlap` and `merge`."""

from __future__ import annotations

import pytest

from sushicore.design import DesignError, TopicMerger, check_design, find_overlap

K_WORK_SPEC = "# Clouds\n\n**Status:** Open — x\n**Implements:** VOLUMETRIC_CLOUDS#A1\n"
K_README_CITING = "See docs/design/VOLUMETRIC_CLOUDS/README.md and docs/design/VOLUMETRIC_CLOUDS/MARCH.md.\n"


def _edit(store, name: str, old: str, new: str) -> None:
    """Replaces text in a topic's document."""
    path = store.topic(name).path
    store.files.write_text(path, store.files.read_text(path).replace(old, new))


def _merged(store):
    """Writes the two topics, a work folder and a README that cite the merged one, and merges."""
    _two_topics(store)
    store.files.write_text(store.root / "docs" / "agent" / "2026_10_28_CLOUDS" / "SPEC.md", K_WORK_SPEC)
    store.files.write_text(store.root / "README.md", K_README_CITING)
    return TopicMerger(store).merge("ATMOSPHERE", "VOLUMETRIC_CLOUDS")


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


@pytest.mark.small
def test_overlap_lists_a_module_two_topics_name(memory_store):
    """A module named by two topics is shared."""
    memory_store.create("ATMOSPHERE", modules=["modules/atmosphere"], about="The air.")
    memory_store.create("CLOUDS", modules=["modules/clouds"], about="The clouds.")
    _edit(memory_store, "CLOUDS", "`modules/clouds`", "`modules/clouds`, `modules/atmosphere`")
    assert find_overlap(memory_store).shared == (("modules/atmosphere", ("ATMOSPHERE", "CLOUDS")),)


@pytest.mark.small
def test_overlap_lists_a_module_inside_another_topics_module(memory_store):
    """A module inside the module of another topic is nested."""
    memory_store.create("ATMOSPHERE", modules=["modules/atmosphere"], about="The air.")
    memory_store.create("DOME", modules=["modules/clouds"], about="The dome.")
    _edit(memory_store, "DOME", "`modules/clouds`", "`modules/atmosphere/sky`")
    assert find_overlap(memory_store).nested == (("modules/atmosphere", "ATMOSPHERE", "modules/atmosphere/sky", "DOME"),)


@pytest.mark.small
def test_overlap_lists_the_word_two_topic_names_share(memory_store):
    """Topics whose names share a word may describe one subject."""
    memory_store.create("ATMOSPHERE", modules=["modules/atmosphere"], about="The air.")
    memory_store.create("ATMOSPHERE_SKY", modules=["modules/clouds"], about="The sky.")
    assert find_overlap(memory_store).words == (("ATMOSPHERE", "ATMOSPHERE_SKY", "ATMOSPHERE"),)


@pytest.mark.medium
def test_merge_makes_the_merged_topic_a_page_without_its_frame(store):
    """The page keeps the prose, and the folder of the merged topic is gone."""
    _merged(store)
    page = (store.design / "ATMOSPHERE" / "VOLUMETRIC_CLOUDS.md").read_text(encoding="utf-8")
    assert "The clouds stretch" in page and "**Status:**" not in page and "| Id |" not in page


@pytest.mark.medium
def test_merge_deletes_the_folder_of_the_merged_topic(store):
    """The merged topic no longer has a folder."""
    _merged(store)
    assert not (store.design / "VOLUMETRIC_CLOUDS").exists()


@pytest.mark.medium
def test_merge_joins_the_phases_and_prefixes_a_clashing_id(store):
    """A phase id both topics have is prefixed by the merged topic."""
    result = _merged(store)
    assert result.renamed_phases == (("A1", "VOLUMETRIC_CLOUDS-A1"),)
    assert [p.ident for p in store.topic("ATMOSPHERE").document.phases] == ["A1", "VOLUMETRIC_CLOUDS-A1", "C2"]


@pytest.mark.medium
def test_merge_joins_the_modules(store):
    """The topic that stays names the modules of both."""
    _merged(store)
    assert store.topic("ATMOSPHERE").document.modules() == ["modules/atmosphere", "modules/clouds"]


@pytest.mark.medium
def test_merge_rewrites_the_phase_citation_of_a_work_folder(store):
    """A work folder that implemented a renamed phase cites the new id."""
    _merged(store)
    work = store.root / "docs" / "agent" / "2026_10_28_CLOUDS" / "SPEC.md"
    assert "ATMOSPHERE#VOLUMETRIC_CLOUDS-A1" in work.read_text(encoding="utf-8")


@pytest.mark.medium
def test_merge_rewrites_the_links_to_the_merged_documents(store):
    """A link to the merged README and to a moved page points at the new place."""
    _merged(store)
    assert (store.root / "README.md").read_text(encoding="utf-8") == (
        "See docs/design/ATMOSPHERE/VOLUMETRIC_CLOUDS.md and docs/design/ATMOSPHERE/MARCH.md.\n")


@pytest.mark.medium
def test_merge_leaves_the_repository_clean(store):
    """After a merge the check finds nothing."""
    _merged(store)
    assert check_design(store) == []


@pytest.mark.medium
@pytest.mark.parametrize(
    ("into", "source", "reason"),
    [("ATMOSPHERE", "ATMOSPHERE", "not merged into itself"), ("ATMOSPHERE", "VOLUMETRIC_CLOUDS", "exists")],
)
def test_merge_refuses_itself_and_a_page_that_exists(store, into, source, reason):
    """A topic is not merged into itself, nor over a page."""
    _two_topics(store)
    (store.design / "ATMOSPHERE" / "VOLUMETRIC_CLOUDS.md").write_text("# x\n", encoding="utf-8")
    with pytest.raises(DesignError, match=reason):
        TopicMerger(store).merge(into, source)


@pytest.mark.medium
def test_merge_renames_a_page_whose_name_is_taken(store):
    """A page of the merged topic that clashes gets its topic's name in front."""
    _two_topics(store)
    (store.design / "ATMOSPHERE" / "MARCH.md").write_text("# Mine\n", encoding="utf-8")
    TopicMerger(store).merge("ATMOSPHERE", "VOLUMETRIC_CLOUDS")
    assert (store.design / "ATMOSPHERE" / "VOLUMETRIC_CLOUDS_MARCH.md").is_file()
    page = (store.design / "ATMOSPHERE" / "VOLUMETRIC_CLOUDS.md").read_text(encoding="utf-8")
    assert "](VOLUMETRIC_CLOUDS_MARCH.md)" in page


@pytest.mark.medium
def test_merge_command_reports_the_page_it_wrote(store, disk_cli):
    """The command prints the page first."""
    _two_topics(store)
    assert disk_cli.run("merge", "ATMOSPHERE", "VOLUMETRIC_CLOUDS") == 0
    assert disk_cli.lines()[0] == "docs/design/ATMOSPHERE/VOLUMETRIC_CLOUDS.md"
