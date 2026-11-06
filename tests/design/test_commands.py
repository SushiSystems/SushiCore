# test_commands.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the `design` group a CLI registers."""

from __future__ import annotations

import json

import pytest

from sushicore.design import OwnedModuleError

pytestmark = pytest.mark.small

K_NEW_ATMOSPHERE = ("new", "ATMOSPHERE", "--modules", "modules/atmosphere", "--about", "The air.")


def test_new_reports_the_document_it_wrote(cli):
    """An agent opens a topic and is told where it is."""
    assert cli.run(*K_NEW_ATMOSPHERE) == 0
    assert cli.lines() == ["docs/design/ATMOSPHERE/README.md"]


def test_list_json_gives_the_modules_of_each_topic(cli):
    """An agent reads the topics as JSON."""
    cli.run(*K_NEW_ATMOSPHERE)
    cli.run("list", "--json")
    assert json.loads(cli.lines()[-1])[0]["modules"] == ["modules/atmosphere"]


def test_owner_names_the_topic_that_owns_a_path(cli):
    """A path inside a module is owned by the topic that names the module."""
    cli.run(*K_NEW_ATMOSPHERE)
    cli.run("owner", "modules/atmosphere/sky")
    assert cli.lines()[-1] == "ATMOSPHERE"


def test_owner_of_an_unowned_path_is_none(cli):
    """A path no topic names has the owner none."""
    cli.run("owner", "modules/clouds")
    assert cli.lines() == ["none"]


def test_new_refuses_an_owned_module(cli):
    """The second topic on a module is refused and the owner is named."""
    cli.run(*K_NEW_ATMOSPHERE)
    with pytest.raises(OwnedModuleError, match="owned by ATMOSPHERE"):
        cli.run("new", "SKY", "--modules", "modules/atmosphere/sky", "--about", "The sky.")


def test_phase_reports_the_phase_as_planned(cli):
    """A phase is added planned."""
    cli.run(*K_NEW_ATMOSPHERE)
    cli.run("phase", "ATMOSPHERE", "A1", "Scatter light")
    assert cli.lines()[-1] == "ATMOSPHERE#A1 planned"


def test_phase_state_ships_the_topic_on_the_day_of_the_clock(cli):
    """The last built phase ships the topic, dated by the clock."""
    cli.run(*K_NEW_ATMOSPHERE)
    cli.run("phase", "ATMOSPHERE", "A1", "Scatter light")
    cli.run("phase-state", "ATMOSPHERE", "A1", "built")
    assert cli.lines()[-1] == "Shipped — 2026-10-28"


def test_check_is_clean_after_a_topic_and_a_phase(cli):
    """What the tool wrote passes the check."""
    cli.run(*K_NEW_ATMOSPHERE)
    cli.run("phase", "ATMOSPHERE", "A1", "Scatter light")
    assert cli.run("check") == 0
    assert cli.lines()[-1] == "clean"


def test_check_exits_1_on_a_module_two_topics_name(cli, memory_store):
    """A hand-made overlap fails the check."""
    cli.run(*K_NEW_ATMOSPHERE)
    cli.run("new", "CLOUDS", "--modules", "modules/clouds", "--about", "Clouds.")
    path = memory_store.topic("CLOUDS").path
    memory_store.files.write_text(
        path, memory_store.files.read_text(path).replace("`modules/clouds`", "`modules/clouds`, `modules/atmosphere`"),
    )
    assert cli.run("check") == 1
    assert "owned by ATMOSPHERE" in cli.lines()[-1]


def test_overlap_lists_a_module_two_topics_name(cli, memory_store):
    """The shared module is named with its topics."""
    cli.run(*K_NEW_ATMOSPHERE)
    cli.run("new", "CLOUDS", "--modules", "modules/clouds", "--about", "Clouds.")
    path = memory_store.topic("CLOUDS").path
    memory_store.files.write_text(
        path, memory_store.files.read_text(path).replace("`modules/clouds`", "`modules/clouds`, `modules/atmosphere`"),
    )
    cli.run("overlap")
    assert cli.lines()[-1] == "shared modules/atmosphere: ATMOSPHERE, CLOUDS"
