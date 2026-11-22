# test_sushi_build_policy.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What sushi_build_policy() sets in a real configure, and that an older CMake stops at it."""

import re
import shutil

import pytest

#: The linker programs CMAKE_LINKER_TYPE LLD runs: GNU-style and MSVC-style.
K_LLD_PROGRAMS = ("ld.lld", "lld-link")


@pytest.mark.medium
def test_build_policy_configures_with_lld_as_the_linker_type(basic_tree):
    assert basic_tree.code == 0, basic_tree.output
    assert basic_tree.says("sushi-probe CMAKE_LINKER_TYPE=LLD"), basic_tree.output


@pytest.mark.medium
def test_build_policy_writes_compile_commands_into_the_tree(basic_tree):
    assert basic_tree.compile_command("probe.cpp")


@pytest.mark.medium
@pytest.mark.skipif(not any(map(shutil.which, K_LLD_PROGRAMS)),
                    reason="neither ld.lld nor lld-link is on the search path")
def test_build_policy_links_a_program_through_lld(basic_tree):
    assert re.search(r"-fuse-ld=lld|lld-link", basic_tree.link_block("probe"))


@pytest.mark.medium
def test_build_policy_stops_a_cmake_older_than_3_29_with_its_message(run_script):
    done = run_script(
        'include("${SUSHI_MODULES}/SushiBuildPolicy.cmake")\n'
        "set(CMAKE_VERSION 3.28.6)\n"
        "set(PROJECT_NAME probe)\n"
        "sushi_build_policy()\n")
    assert done.code != 0
    assert done.says("needs CMake 3.29 or later; this configure runs CMake 3.28.6"), done.output
