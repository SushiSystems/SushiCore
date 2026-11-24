# test_pin_text.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for pointing a pin at a new tag."""

import pytest

from sushicore.release_train.pin_text import pin_in_deps, pin_in_workflow
from sushicore.release_train.version import Version

pytestmark = pytest.mark.small

K_DEPS = ('[sushisystems.sushilog]\nversion = "v0.5.1"\ncommit  = "aaa"\n\n'
          '[sushisystems.sushiprofiler]\nversion = "v0.5.1"\ncommit  = "bbb"\n')


def test_only_the_table_of_the_library_moves():
    assert pin_in_deps(K_DEPS, "sushilog", Version(0, 5, 2), "ccc") == K_DEPS.replace(
        'v0.5.1"\ncommit  = "aaa"', 'v0.5.2"\ncommit  = "ccc"')


def test_a_workflow_variable_of_the_library_moves():
    text = "env:\n  SUSHIRUNTIME_REF: v0.7.1\n  SUSHIBLAS_REF: v0.3.0\n"
    assert pin_in_workflow(text, "sushiruntime", Version(0, 7, 2)) == text.replace("v0.7.1", "v0.7.2")
