# test_backend_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What the in-memory toolkit locator promises beyond the locator contract in test_backend.py."""

from __future__ import annotations

import pathlib
from types import SimpleNamespace

import pytest

from sushicore.provision.gpu.backend import ToolkitInstall
from sushicore.provision.gpu.backend_memory import InMemoryToolkitLocator

pytestmark = pytest.mark.small

_CFG = SimpleNamespace(platform="linux")


def test_a_locator_with_no_install_finds_none():
    assert InMemoryToolkitLocator().locate(_CFG) is None


def test_provision_returns_the_outcome_the_locator_was_built_with():
    assert InMemoryToolkitLocator(provisioned=False).provision(_CFG, dry_run=False) is False


def test_provision_records_the_configuration_and_the_dry_run_flag():
    locator = InMemoryToolkitLocator(ToolkitInstall(pathlib.Path("/t"), None))
    locator.provision(_CFG, dry_run=True)
    assert locator.provisioned_with == [(_CFG, True)]


def test_locate_records_each_configuration_it_was_asked_about():
    locator = InMemoryToolkitLocator()
    locator.locate(_CFG)
    assert locator.located == [_CFG]


def test_a_locator_told_to_fail_raises_on_locate_and_records_the_call():
    locator = InMemoryToolkitLocator(fail_with=OSError("disk unreadable"))

    with pytest.raises(OSError):
        locator.locate(_CFG)

    assert locator.located == [_CFG]
