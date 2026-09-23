# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the stock doctor checks."""

from __future__ import annotations

import sys

from sushicore.provision import checks
from sushicore.provision.doctor import State


def test_python_check_passes_on_this_interpreter():
    result = checks.python_check((3, 10)).run()
    assert result.state is State.OK
    assert sys.executable in result.detail


def test_tool_check_fails_with_the_fix_for_a_missing_tool():
    result = checks.tool_check("x", "sushi-no-such-tool", fix="st setup").run()
    assert result.state is State.FAIL
    assert result.fix == "st setup"


def test_python_module_check_finds_the_stdlib():
    assert checks.python_module_check("json", "eval", True, "").run().state is State.OK


def test_missing_python_module_fails():
    result = checks.python_module_check("sushi_no_such_mod", "infer", True, "pip install x").run()
    assert result.state is State.FAIL


def test_path_check_reports_the_missing_path(tmp_path):
    result = checks.path_check("yolox", tmp_path / "nope", "infer", True, "git submodule update").run()
    assert result.state is State.FAIL and "nope" in result.detail


def test_stamp_check_warns_on_an_unstamped_toolchain(tmp_path):
    (tmp_path / "toolchains" / "llvm-sycl").mkdir(parents=True)
    assert checks.stamp_check(tmp_path).run().state is State.WARN
