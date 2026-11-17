# test_base.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the host contract."""

from __future__ import annotations

import pytest

from sushicore.provision.host import IHost


@pytest.mark.small
def test_the_host_contract_cannot_be_instantiated():
    """Check that IHost stays abstract, so every host implements every method."""
    with pytest.raises(TypeError):
        IHost()  # type: ignore[abstract]
