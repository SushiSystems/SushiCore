# test_store.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the design store: topics, module ownership, and opening a topic, a page or a phase."""

from __future__ import annotations

import datetime
from pathlib import Path

import pytest

from sushicore.design import DesignError, DesignStore, OwnedModuleError
from sushicore.files_memory import MemoryFiles

@pytest.mark.medium
def test_new_topic_owns_its_modules_and_refuses_a_second_owner(store):
    """A module belongs to one topic; a module inside it is a page of that topic."""
    store.create("ATMOSPHERE", modules=["modules/atmosphere"], about="The air.")
    assert store.owner("modules/atmosphere/sky/sky.cpp") == "ATMOSPHERE"
    assert store.owner("modules/clouds") is None
    with pytest.raises(OwnedModuleError, match="owned by ATMOSPHERE"):
        store.create("SKY", modules=["modules/atmosphere/sky"], about="The sky.")
    with pytest.raises(OwnedModuleError):
        store.create("WORLD", modules=["modules"], about="Everything.")


@pytest.mark.medium
def test_new_refuses_a_bad_name_a_taken_name_a_missing_module_and_no_about(store):
    """Each refusal names what is wrong."""
    store.create("ATMOSPHERE", modules=["modules/atmosphere"], about="The air.")
    for name, modules, about in (
        ("Atmosphere", [], "x"), ("ATMOSPHERE", [], "x"), ("RAIN", ["modules/rain"], "x"), ("RAIN", [], " "),
    ):
        with pytest.raises(DesignError):
            store.create(name, modules=modules, about=about)


@pytest.mark.medium
def test_deepest_named_module_owns_a_path(store, tmp_path):
    """With nested modules, the deeper one wins."""
    store.create("ATMOSPHERE", modules=["modules/atmosphere"], about="The air.")
    topic = store.topic("ATMOSPHERE").path
    sky = store.design / "SKY" / "README.md"
    sky.parent.mkdir()
    sky.write_text(topic.read_text(encoding="utf-8").replace("`modules/atmosphere`", "`modules/atmosphere/sky`"), encoding="utf-8")
    assert store.owner("modules/atmosphere/sky/a.cpp") == "SKY"


@pytest.mark.medium
def test_page_and_phase_and_shipping(store):
    """A page sits beside the README; the topic ships when its last phase is built."""
    store.create("ATMOSPHERE", modules=["modules/atmosphere"], about="The air.")
    page = store.add_page("ATMOSPHERE", "clouds")
    assert page.name == "CLOUDS.md"
    store.add_phase("ATMOSPHERE", "A1", "Scatter light")
    store.add_phase("ATMOSPHERE", "A2", "Draw clouds")
    with pytest.raises(DesignError):
        store.add_phase("ATMOSPHERE", "A1", "Again")
    assert store.set_phase_state("ATMOSPHERE", "A1", "built").startswith("Open")
    assert store.set_phase_state("ATMOSPHERE", "A2", "withdrawn") == "Shipped — 2026-10-28"
    store.add_phase("ATMOSPHERE", "A3", "Rain")
    assert store.topic("ATMOSPHERE").document.status == "**Status:** Open — phases A3 to be built"


@pytest.mark.medium
def test_open_documents_leave_out_topics_under_revision(store):
    """A topic in _REVISION is not counted as open work."""
    store.create("ATMOSPHERE", modules=["modules/atmosphere"], about="The air.")
    held = store.design / "_REVISION" / "OLD" / "README.md"
    held.parent.mkdir(parents=True)
    held.write_text("# Old\n\n**Status:** Open — held\n", encoding="utf-8")
    assert [path.parent.name for path in store.open_documents()] == ["ATMOSPHERE"]
    assert "OLD" in store.topic_paths()


@pytest.mark.medium
def test_a_topic_under_revision_owns_no_module(store):
    """A frozen topic does not stop a live one from owning its module."""
    held = store.design / "_REVISION" / "OLD" / "README.md"
    held.parent.mkdir(parents=True)
    held.write_text("# Old\n\n**Status:** Open — held\n**Modules:** `modules/atmosphere`\n", encoding="utf-8")
    assert store.owners() == {}
    store.create("ATMOSPHERE", modules=["modules/atmosphere"], about="The air.")
    assert store.owner("modules/atmosphere") == "ATMOSPHERE"


@pytest.mark.small
def test_a_topic_is_created_and_owned_with_no_disk():
    """The store keeps its promise on the in-memory files: it writes, finds and reads a topic."""
    root = Path("repo")
    files = MemoryFiles({root / "modules" / "atmosphere" / "CMakeLists.txt": ""})
    store = DesignStore(root, lambda: datetime.date(2026, 10, 28), files)
    path = store.create("ATMOSPHERE", modules=["modules/atmosphere"], about="The air.")
    assert files.is_file(path)
    assert store.owner("modules/atmosphere/sky.cpp") == "ATMOSPHERE"
    assert [topic.name for topic in store.topics()] == ["ATMOSPHERE"]
