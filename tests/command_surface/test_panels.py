# test_panels.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests that every canonical verb has one panel and that a CLI adds at most one domain panel."""

import pytest

from sushicore.command_surface import (K_CANONICAL_VERBS, K_VERB_PANELS, CommandPanels, DomainPanelError,
                                       UnknownVerbError, panel_of)

pytestmark = pytest.mark.small


def test_panel_map_covers_every_canonical_verb_and_nothing_else():
    assert set(K_VERB_PANELS) == set(K_CANONICAL_VERBS)


@pytest.mark.parametrize(("verb", "panel"), [
    ("build", "Build"), ("check", "Build"), ("run", "Run"), ("bench", "Run"),
    ("setup", "Environment"), ("env", "Environment"), ("backlog", "Records"), ("design", "Records"),
])
def test_panel_of_names_the_panel_the_guide_gives_the_verb(verb, panel):
    assert panel_of(verb) == panel


def test_panel_of_refuses_a_verb_that_is_not_canonical():
    with pytest.raises(UnknownVerbError, match="deploy"):
        panel_of("deploy")


def test_panels_without_a_domain_list_the_four_canonical_ones():
    assert CommandPanels().order() == ("Build", "Run", "Environment", "Records")


def test_panels_place_the_domain_panel_after_run():
    assert CommandPanels("Models").order() == ("Build", "Run", "Models", "Environment", "Records")


@pytest.mark.parametrize("domain", ["", "  ", "Build", "Records"])
def test_panels_refuse_an_empty_domain_or_one_named_like_a_canonical_panel(domain):
    with pytest.raises(DomainPanelError):
        CommandPanels(domain)
