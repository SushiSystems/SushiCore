# test_tree_reuse.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""A build refuses a tree CMake cannot configure again, and accepts every other tree."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.cmake_driver_memory import MemoryCMakeDriver
from sushicore.console_memory import RecordingConsole
from sushicore.errors import ConfigError
from sushicore.tree_reuse import refuse_unreusable_tree

_ROOT = Path("checkout")
_TREE = _ROOT / "build" / "default-debug"


def _driver(**tree) -> MemoryCMakeDriver:
    return MemoryCMakeDriver(RecordingConsole()).add_tree(_TREE, **tree)


def _refuse(driver, generator: str = "Ninja", root: Path = _ROOT) -> None:
    refuse_unreusable_tree(driver, _TREE, generator=generator, root=root, program="xx")


@pytest.mark.small
def test_a_tree_that_is_not_there_is_accepted():
    """Checks a first build, which has no tree to refuse, goes ahead."""
    _refuse(MemoryCMakeDriver(RecordingConsole()))


@pytest.mark.small
def test_a_tree_of_the_generator_the_build_uses_is_accepted():
    _refuse(_driver(generator="Ninja"))


@pytest.mark.small
def test_another_generator_is_refused_and_the_message_points_at_clean():
    with pytest.raises(ConfigError) as error:
        _refuse(_driver(generator="Unix Makefiles"))

    assert "configured with Unix Makefiles" in str(error.value)
    assert "`xx clean`" in str(error.value)


@pytest.mark.small
@pytest.mark.parametrize(("configured", "refused"), [
    ("Unix Makefiles", False), ("Visual Studio 17 2022", False), ("Ninja", True)])
def test_the_platform_default_accepts_its_own_families_only(configured, refused):
    driver = _driver(generator=configured)

    if refused:
        with pytest.raises(ConfigError):
            _refuse(driver, generator="")
    else:
        _refuse(driver, generator="")


@pytest.mark.small
def test_a_tree_configured_for_another_source_folder_is_refused():
    driver = _driver(cache={"CMAKE_HOME_DIRECTORY": "/workspace"})

    with pytest.raises(ConfigError) as error:
        _refuse(driver)

    assert "another source folder" in str(error.value)


@pytest.mark.small
def test_a_tree_of_this_source_folder_is_accepted():
    _refuse(_driver(cache={"CMAKE_HOME_DIRECTORY": str(_ROOT)}))
