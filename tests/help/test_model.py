# test_model.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests the model a help screen is drawn from."""

import dataclasses

import pytest

from sushicore.help.model import HelpModel, HelpSection

pytestmark = pytest.mark.small


def test_a_help_model_is_frozen():
    section = HelpSection("Commands", (("build", "Build it."),))
    model = HelpModel("sx", "A tool.", "sx [OPTIONS]", True, (section,), (), (), ())
    with pytest.raises(dataclasses.FrozenInstanceError):
        model.name = "other"
    assert model.commands[0].entries == (("build", "Build it."),)
