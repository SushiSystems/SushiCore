# test_sushi_test_sizes.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What the step of sushi_check_test_sizes() and its script do in a real tree."""

import pytest


@pytest.mark.medium
def test_check_test_sizes_adds_a_step_the_program_builds_after(basic_tree):
    rules = (basic_tree.tree / "build.ninja").read_text(encoding="utf-8")
    assert "Checking the test sizes of probe" in rules


@pytest.mark.medium
def test_check_test_sizes_passes_sources_whose_suites_carry_a_size(basic_tree, build_target):
    built = build_target(basic_tree, "probe_sizes")
    assert built.code == 0, built.output
    assert (basic_tree.tree / "probe_sizes.stamp").is_file()


@pytest.mark.medium
def test_check_test_sizes_fails_the_build_at_a_suite_without_a_size(configure, build_target):
    built = build_target(configure("basic", "-DBASIC_SUITES=suites_unsized.cpp"), "probe_sizes")
    assert built.code != 0
    assert built.says("the suite Probe carries no size"), built.output
