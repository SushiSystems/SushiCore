# test_options.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests that the options a CLI with its own test command takes from the package are spelled alike."""

import pytest

from sushicore.testing import all_option, filter_option, jobs_option, label_option, repeat_option

pytestmark = pytest.mark.small


def test_the_shared_options_carry_the_names_every_cli_spells_alike():
    spelled = [option.param_decls for option in (label_option(), filter_option(), repeat_option(),
                                                 jobs_option(), all_option())]
    assert spelled == [("--label", "-l"), ("--filter", "-f"), ("--repeat", "-r"), ("--jobs", "-j"), ("--all",)]
