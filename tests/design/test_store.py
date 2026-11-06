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

pytestmark = pytest.mark.small

K_HELD = "# Old\n\n**Status:** Open — held\n**Modules:** `modules/atmosphere`\n"


def _atmosphere(store) -> None:
    """Opens the topic ATMOSPHERE on the module atmosphere."""
    store.create("ATMOSPHERE", modules=["modules/atmosphere"], about="The air.")


def _atmosphere_with_two_phases(store) -> None:
    """Opens ATMOSPHERE with the planned phases A1 and A2."""
    _atmosphere(store)
    store.add_phase("ATMOSPHERE", "A1", "Scatter light")
    store.add_phase("ATMOSPHERE", "A2", "Draw clouds")


def test_a_path_inside_a_module_is_owned_by_its_topic(memory_store):
    """A module belongs to one topic; a path inside it is that topic's."""
    _atmosphere(memory_store)
    assert memory_store.owner("modules/atmosphere/sky/sky.cpp") == "ATMOSPHERE"


def test_a_path_in_no_topics_module_has_no_owner(memory_store):
    """A module no topic names has no owner."""
    _atmosphere(memory_store)
    assert memory_store.owner("modules/clouds") is None


def test_new_refuses_a_module_inside_an_owned_module(memory_store):
    """A second topic on a module inside an owned one is refused, naming the owner."""
    _atmosphere(memory_store)
    with pytest.raises(OwnedModuleError, match="owned by ATMOSPHERE"):
        memory_store.create("SKY", modules=["modules/atmosphere/sky"], about="The sky.")


def test_new_refuses_a_module_that_contains_an_owned_module(memory_store):
    """A second topic on a module around an owned one is refused."""
    _atmosphere(memory_store)
    with pytest.raises(OwnedModuleError, match="owned by ATMOSPHERE"):
        memory_store.create("WORLD", modules=["modules"], about="Everything.")


@pytest.mark.parametrize(
    ("name", "modules", "about", "reason"),
    [
        ("Atmosphere", [], "x", "is not a topic name"),
        ("ATMOSPHERE", [], "x", "the topic ATMOSPHERE exists"),
        ("RAIN", ["modules/rain"], "x", "'modules/rain' is not in the repository"),
        ("RAIN", [], " ", "--about"),
    ],
)
def test_new_refuses_what_is_wrong_and_names_it(memory_store, name, modules, about, reason):
    """Each refusal names what is wrong."""
    _atmosphere(memory_store)
    with pytest.raises(DesignError, match=reason):
        memory_store.create(name, modules=modules, about=about)


def test_deepest_named_module_owns_a_path(memory_store):
    """With nested modules, the deeper one wins."""
    _atmosphere(memory_store)
    topic = memory_store.topic("ATMOSPHERE").path
    text = memory_store.files.read_text(topic).replace("`modules/atmosphere`", "`modules/atmosphere/sky`")
    memory_store.files.write_text(memory_store.design / "SKY" / "README.md", text)
    assert memory_store.owner("modules/atmosphere/sky/a.cpp") == "SKY"


def test_a_page_sits_beside_the_readme(memory_store):
    """A page is written upper case beside the README."""
    _atmosphere(memory_store)
    assert memory_store.add_page("ATMOSPHERE", "clouds") == memory_store.design / "ATMOSPHERE" / "CLOUDS.md"


def test_a_phase_id_taken_is_refused(memory_store):
    """A topic has each phase id once."""
    _atmosphere(memory_store)
    memory_store.add_phase("ATMOSPHERE", "A1", "Scatter light")
    with pytest.raises(DesignError, match="has a phase A1"):
        memory_store.add_phase("ATMOSPHERE", "A1", "Again")


def test_a_topic_with_a_phase_left_stays_open(memory_store):
    """Building one of two phases leaves the topic open."""
    _atmosphere_with_two_phases(memory_store)
    assert memory_store.set_phase_state("ATMOSPHERE", "A1", "built").startswith("Open")


def test_a_topic_ships_when_its_last_phase_is_built_or_withdrawn(memory_store):
    """The status is Shipped, dated by the clock, once no phase is open."""
    _atmosphere_with_two_phases(memory_store)
    memory_store.set_phase_state("ATMOSPHERE", "A1", "built")
    assert memory_store.set_phase_state("ATMOSPHERE", "A2", "withdrawn") == "Shipped — 2026-10-28"


def test_a_new_phase_reopens_a_shipped_topic(memory_store):
    """A phase added to a shipped topic opens it again."""
    _atmosphere(memory_store)
    memory_store.add_phase("ATMOSPHERE", "A1", "Scatter light")
    memory_store.set_phase_state("ATMOSPHERE", "A1", "built")
    memory_store.add_phase("ATMOSPHERE", "A3", "Rain")
    assert memory_store.topic("ATMOSPHERE").document.status == "**Status:** Open — phases A3 to be built"


def test_open_documents_leave_out_topics_under_revision(memory_store):
    """A topic in _REVISION is not counted as open work."""
    _atmosphere(memory_store)
    memory_store.files.write_text(memory_store.design / "_REVISION" / "OLD" / "README.md", "# Old\n\n**Status:** Open — held\n")
    assert [path.parent.name for path in memory_store.open_documents()] == ["ATMOSPHERE"]


def test_topic_paths_include_topics_under_revision(memory_store):
    """A topic in _REVISION is still a topic."""
    memory_store.files.write_text(memory_store.design / "_REVISION" / "OLD" / "README.md", "# Old\n\n**Status:** Open — held\n")
    assert "OLD" in memory_store.topic_paths()


def test_a_topic_under_revision_owns_no_module(memory_store):
    """A frozen topic owns nothing."""
    memory_store.files.write_text(memory_store.design / "_REVISION" / "OLD" / "README.md", K_HELD)
    assert memory_store.owners() == {}


def test_a_live_topic_may_take_a_module_a_frozen_topic_names(memory_store):
    """A frozen topic does not stop a live one from owning its module."""
    memory_store.files.write_text(memory_store.design / "_REVISION" / "OLD" / "README.md", K_HELD)
    _atmosphere(memory_store)
    assert memory_store.owner("modules/atmosphere") == "ATMOSPHERE"


def test_a_topic_is_created_and_owned_with_no_disk():
    """The store keeps its promise on the in-memory files: it writes, finds and reads a topic."""
    root = Path("repo")
    files = MemoryFiles({root / "modules" / "atmosphere" / "CMakeLists.txt": ""})
    store = DesignStore(root, lambda: datetime.date(2026, 10, 28), files)
    path = store.create("ATMOSPHERE", modules=["modules/atmosphere"], about="The air.")
    assert files.is_file(path)
    assert store.owner("modules/atmosphere/sky.cpp") == "ATMOSPHERE"
    assert [topic.name for topic in store.topics()] == ["ATMOSPHERE"]
