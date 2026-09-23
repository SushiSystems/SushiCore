# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the stock doctor checks."""

from __future__ import annotations

import sys

from sushicore.provision import checks
from sushicore.provision.doctor import State
from sushicore.provision.fragments import Dependency, IDependencySource


class _FixedSource(IDependencySource):
    """A dependency source returning a fixed list, unfiltered by platform or GPU."""

    def __init__(self, deps: list[Dependency]) -> None:
        """Store the dependencies this source always returns."""
        self._deps = deps

    def all(self) -> list[Dependency]:
        """Return every stored dependency."""
        return list(self._deps)

    def selected(self, platform: str, gpu: bool) -> list[Dependency]:
        """Return every stored dependency, ignoring *platform* and *gpu*."""
        del platform, gpu
        return list(self._deps)


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


def test_fragment_check_fails_a_dependency_whose_check_cmd_hangs(monkeypatch):
    monkeypatch.setattr(checks, "_VERSION_TIMEOUT", 0.1)
    dep = Dependency(name="slow", check_cmd=[sys.executable, "-c", "import time; time.sleep(5)"])
    result = checks.fragment_check(_FixedSource([dep]), "linux", False, "").run()
    assert result.state is State.FAIL
    assert "slow" in result.detail


def test_fragment_check_fails_a_malformed_check_cmd():
    dep = Dependency(name="broken", check_cmd=42)
    result = checks.fragment_check(_FixedSource([dep]), "linux", False, "").run()
    assert result.state is State.FAIL
    assert "broken" in result.detail
