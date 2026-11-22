# test_sushi_abi_pinning.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What sushi_pin_abi() sets in a real configure, and that the module refuses an old CMP0091."""

import pytest


@pytest.mark.medium
def test_pin_abi_takes_the_release_runtime_for_every_build_type(basic_tree):
    assert basic_tree.says("sushi-probe CMAKE_MSVC_RUNTIME_LIBRARY=MultiThreadedDLL")


@pytest.mark.medium
def test_pin_abi_maps_a_debug_consumer_to_the_release_imports(basic_tree):
    mapped = "Release;RelWithDebInfo;MinSizeRel;None;"
    assert basic_tree.says(f"sushi-probe CMAKE_MAP_IMPORTED_CONFIG_DEBUG={mapped}")


@pytest.mark.medium
def test_abi_pinning_refuses_an_includer_whose_cmp0091_is_old(run_script):
    done = run_script(
        "cmake_policy(SET CMP0091 OLD)\n"
        'include("${SUSHI_MODULES}/SushiAbiPinning.cmake")\n')
    assert done.code != 0
    assert done.says("policy CMP0091 is 'OLD'"), done.output
