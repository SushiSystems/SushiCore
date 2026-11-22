# test_sushi_sanitizers.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What the sanitizer target of sushi_sanitizers() hands a program in a real configure."""

import pytest


@pytest.mark.medium
def test_sanitizers_add_no_flag_by_default(basic_tree):
    assert "-fsanitize" not in basic_tree.compile_command("probe.cpp")


@pytest.mark.medium
def test_sanitizers_compile_the_named_set_and_stop_at_undefined_behaviour(configure):
    configured = configure("basic", "-DBASIC_SANITIZE=address,undefined")
    command = configured.compile_command("probe.cpp")
    assert "-fsanitize=address,undefined" in command
    assert "-fno-sanitize-recover=undefined" in command


@pytest.mark.medium
def test_sanitizers_refuse_a_value_that_is_not_a_list_of_names(configure):
    configured = configure("basic", "-DBASIC_SANITIZE=address;thread!")
    assert configured.code != 0
    assert configured.says("is not a comma-separated list of sanitizer names"), configured.output
