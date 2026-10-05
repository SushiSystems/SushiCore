# test_config.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026 Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests for the configuration shape provision code reads."""

from __future__ import annotations

import re
from pathlib import Path

import sushicore.provision as provision
from sushicore.provision.config import ProvisionConfig

_ROOT = Path(provision.__file__).parent
_CFG_ATTRIBUTE = re.compile(r"\bcfg\.([a-z_]+)")


def _declared() -> set[str]:
    """Return every field, property and method name :class:`ProvisionConfig` declares."""
    return set(ProvisionConfig.__annotations__) | {
        name for name in vars(ProvisionConfig) if not name.startswith("_")}


def test_every_config_attribute_provision_reads_is_declared():
    """Check that every config attribute provision reads is declared."""
    read = set()
    for path in _ROOT.rglob("*.py"):
        read.update(_CFG_ATTRIBUTE.findall(path.read_text(encoding="utf-8")))
    assert read - _declared() == set()
