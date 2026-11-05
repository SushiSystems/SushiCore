# test_diag_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""What the in-memory config module promises beyond the contract in test_diag.py."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from sushicore.diag_memory import InMemoryConfigModule

pytestmark = pytest.mark.small

K_ROOT = Path("project")


@dataclass
class _Settings:
    cxx: str = ""
    generator: str = "Ninja"


def test_the_config_directory_defaults_to_cli_below_the_root():
    assert InMemoryConfigModule(K_ROOT, _Settings).config_dir() == K_ROOT / "cli"


def test_the_loaded_config_carries_the_values_given():
    module = InMemoryConfigModule(K_ROOT, _Settings, {"cxx": "clang"})
    assert module.load_config() == _Settings(cxx="clang")


def test_the_sources_default_to_the_two_files_of_the_config_directory():
    module = InMemoryConfigModule(K_ROOT, _Settings)
    assert module.sources() == [K_ROOT / "cli" / "config.toml",
                                K_ROOT / "cli" / "config.local.toml"]


def test_the_sources_are_the_files_given_in_their_order():
    files = [K_ROOT / "b.toml", K_ROOT / "a.toml"]
    assert InMemoryConfigModule(K_ROOT, _Settings, sources=files).sources() == files

