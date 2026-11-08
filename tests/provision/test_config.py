# test_config.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The provision settings a store of built packages is configured from."""

from __future__ import annotations

import pytest

from sushicore.provision.config import ProvisionSettings
from sushicore.provision.sushi_packages.clock_memory import ManualClock
from sushicore.provision.sushi_packages.package_store import PackageStore

from .sushi_packages.package_fakes import install, make_key


@pytest.mark.medium
def test_a_store_configured_from_the_settings_prunes_all_but_three_packages(tmp_path):
    """Check that a store keeping the default package_keep prunes the oldest of four packages."""
    clock = ManualClock()
    store = PackageStore(tmp_path / "packages", keep=ProvisionSettings().package_keep,
                         clock=clock, sleep=lambda _s: None)
    keys = []
    for index in range(4):
        key = make_key("sushiruntime", source=f"s{index}")
        install(store, key)
        keys.append(key)
        clock.advance(60)

    assert store.prune("sushiruntime") == [keys[0].digest()]
