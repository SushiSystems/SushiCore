# test_windows_installer_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""What the in-memory machine environment promises beyond the contract in test_windows_installer.py."""

from __future__ import annotations

import pytest

from sushicore.provision.gpu.windows_installer_memory import InMemoryMachineEnvironment

pytestmark = pytest.mark.small


def test_a_variable_set_to_an_empty_value_reads_as_none():
    assert InMemoryMachineEnvironment({"Path": ""}).read("Path") is None


def test_the_environment_does_not_follow_later_changes_to_the_dictionary_it_was_given():
    variables = {"OS": "Windows_NT"}
    environment = InMemoryMachineEnvironment(variables)
    variables["OS"] = "other"
    assert environment.read("OS") == "Windows_NT"
