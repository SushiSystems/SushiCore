# test_version_text.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for rewriting the version a file declares."""

import pytest

from sushicore.release_train.version import Version
from sushicore.release_train.version_text import bump_text

pytestmark = pytest.mark.small

K_OLD = Version(0, 7, 1)
K_NEW = Version(0, 7, 2)


def test_the_dotted_number_is_rewritten_wherever_it_stands_alone():
    text = 'project(X VERSION 0.7.1 LANGUAGES CXX)\nversion = "0.7.1"\nPROJECT_NUMBER = "v0.7.1"\n'
    assert bump_text(text, K_OLD, K_NEW) == text.replace("0.7.1", "0.7.2")


def test_a_longer_number_that_holds_the_old_one_is_left():
    assert bump_text("10.7.1 and 0.7.12\n", K_OLD, K_NEW) == "10.7.1 and 0.7.12\n"


def test_a_macro_per_part_takes_the_part_that_changed():
    text = "#define X_VERSION_MINOR 7\n#define X_VERSION_PATCH 1\ninline constexpr int K_VERSION_PATCH = 1;\n"
    assert bump_text(text, K_OLD, K_NEW) == text.replace("PATCH 1", "PATCH 2").replace("= 1;", "= 2;")
