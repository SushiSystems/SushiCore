# test_machine_actions.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the replaceable machine calls of the install steps."""

from __future__ import annotations

import dataclasses

import pytest

from sushicore.provision.machine_actions import MachineActions

pytestmark = pytest.mark.small


def test_a_default_which_finds_nothing_for_a_name_no_machine_has():
    assert MachineActions().which("a-program-no-machine-has-0f3a") is None


def test_a_replaced_call_is_the_one_the_actions_hold():
    actions = MachineActions(which=lambda name: f"/bin/{name}", detect_vendor=lambda: "amd")
    assert (actions.which("cc"), actions.detect_vendor()) == ("/bin/cc", "amd")


def test_a_replacement_leaves_the_other_defaults_in_place():
    assert MachineActions(which=lambda name: None).run_command is MachineActions().run_command


def test_the_actions_are_frozen():
    with pytest.raises(dataclasses.FrozenInstanceError):
        MachineActions().which = lambda name: None


def test_the_actions_name_the_seven_machine_calls():
    assert [field.name for field in dataclasses.fields(MachineActions)] == [
        "refresh_path", "which", "find_vcvars", "run_command",
        "resolve_config", "install_oneapi", "detect_vendor",
    ]
