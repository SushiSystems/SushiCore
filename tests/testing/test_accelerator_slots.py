# test_accelerator_slots.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the CTest resource file that shares out the accelerators of the machine."""

import json
from pathlib import Path

import pytest

from sushicore.files_memory import MemoryFiles
from sushicore.testing.accelerator_slots import resource_spec_text, write_resource_spec

pytestmark = pytest.mark.small


def test_each_accelerator_gets_one_slot_under_the_resource_the_shards_name():
    spec = json.loads(resource_spec_text(2))
    assert spec == {"version": {"major": 1, "minor": 0},
                    "local": [{"gpus": [{"id": "0", "slots": 1}, {"id": "1", "slots": 1}]}]}


def test_the_file_is_written_beside_the_run_results_of_the_tree():
    files = MemoryFiles()
    path = write_resource_spec(Path("/repo/build"), files)
    assert path == Path("/repo/build/Testing/resources.json")
    assert json.loads(files.read_text(path))["local"] == [{"gpus": [{"id": "0", "slots": 1}]}]
