# test_verbs.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests that the canonical verb list names each verb once and carries the shared command groups."""

import pytest

from sushicore.command_groups import K_GROUPS
from sushicore.command_surface import K_CANONICAL_VERBS

pytestmark = pytest.mark.small


def test_canonical_verbs_name_each_verb_once():
    assert len(set(K_CANONICAL_VERBS)) == len(K_CANONICAL_VERBS)


def test_canonical_verbs_carry_the_groups_every_cli_adds():
    assert set(K_GROUPS) <= set(K_CANONICAL_VERBS)
