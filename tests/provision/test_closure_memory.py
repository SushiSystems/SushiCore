# test_closure_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What the table locator promises: it answers from its table and nothing else."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.provision.closure_memory import TableLocator


@pytest.mark.small
def test_a_module_in_the_table_is_located():
    assert TableLocator({"sushilog": Path("/ws/sushilog")})("sushilog") == Path("/ws/sushilog")


@pytest.mark.small
def test_a_module_outside_the_table_is_not_located():
    assert TableLocator({"sushilog": Path("/ws/sushilog")})("sushiai") is None
