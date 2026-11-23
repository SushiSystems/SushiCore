# test_sushi_sycl_target.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""How the SYCL target module shapes device options, read from a CMake script run."""

import pytest


@pytest.mark.medium
def test_source_options_split_a_shell_group_into_its_words(run_script):
    done = run_script(
        'include("${SUSHI_MODULES}/SushiSyclTarget.cmake")\n'
        'sushi_sycl_source_options(options -fsycl "SHELL:-Xarch_device -O3")\n'
        'message(STATUS "options=[${options}]")\n')
    assert done.code == 0, done.output
    assert done.says("options=[-fsycl;-Xarch_device;-O3]"), done.output


@pytest.mark.medium
def test_source_options_keep_a_plain_option_with_a_space_whole(run_script):
    done = run_script(
        'include("${SUSHI_MODULES}/SushiSyclTarget.cmake")\n'
        'sushi_sycl_source_options(options "--cuda-path=C:/Program Files/CUDA")\n'
        'message(STATUS "options=[${options}]")\n')
    assert done.code == 0, done.output
    assert done.says("options=[--cuda-path=C:/Program Files/CUDA]"), done.output
