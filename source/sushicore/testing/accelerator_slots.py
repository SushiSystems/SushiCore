# accelerator_slots.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Writes the CTest resource file that gives each accelerator of the machine one test at a time."""

from __future__ import annotations

import json
from pathlib import Path

from ..files import Files

#: The accelerators a test run shares out: the one the machines that run the tests carry.
K_ACCELERATORS = 1

#: The resource a shard that runs on a real accelerator names in its ``RESOURCE_GROUPS``.
K_RESOURCE = "gpus"


def resource_spec_text(accelerators: int = K_ACCELERATORS) -> str:
    """Return a CTest resource specification with one slot on each of *accelerators* accelerators."""
    slots = [{"id": str(index), "slots": 1} for index in range(accelerators)]
    return json.dumps({"version": {"major": 1, "minor": 0}, "local": [{K_RESOURCE: slots}]}, indent=2) + "\n"


def resource_spec_file(tree: Path) -> Path:
    """Return where the resource file of a run over *tree* is written."""
    return tree / "Testing" / "resources.json"


def write_resource_spec(tree: Path, files: Files, accelerators: int = K_ACCELERATORS) -> Path:
    """Write the resource file of a run over *tree* and return its path."""
    path = resource_spec_file(tree)
    files.write_text(path, resource_spec_text(accelerators))
    return path
