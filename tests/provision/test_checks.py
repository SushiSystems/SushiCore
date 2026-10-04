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
    """Check that python check passes on this interpreter."""
    result = checks.python_check((3, 10)).run()
    assert result.state is State.OK
    assert sys.executable in result.detail


def test_tool_check_fails_with_the_fix_for_a_missing_tool():
    """Check that tool check fails with the fix for a missing tool."""
    result = checks.tool_check("x", "sushi-no-such-tool", fix="st setup").run()
    assert result.state is State.FAIL
    assert result.fix == "st setup"


def test_python_module_check_finds_the_stdlib():
    """Check that python module check finds the stdlib."""
    assert checks.python_module_check("json", "eval", True, "").run().state is State.OK


def test_missing_python_module_fails():
    """Check that missing python module fails."""
    result = checks.python_module_check("sushi_no_such_mod", "infer", True, "pip install x").run()
    assert result.state is State.FAIL


def test_path_check_reports_the_missing_path(tmp_path):
    """Check that path check reports the missing path."""
    result = checks.path_check("yolox", tmp_path / "nope", "infer", True, "git submodule update").run()
    assert result.state is State.FAIL and "nope" in result.detail


def test_stamp_check_warns_on_an_unstamped_toolchain(tmp_path):
    """Check that stamp check warns on an unstamped toolchain."""
    (tmp_path / "toolchains" / "llvm-sycl").mkdir(parents=True)
    assert checks.stamp_check(tmp_path).run().state is State.WARN


def test_fragment_check_fails_a_dependency_whose_check_cmd_hangs(monkeypatch):
    """Check that fragment check fails a dependency whose check cmd hangs."""
    monkeypatch.setattr(checks, "_VERSION_TIMEOUT", 0.1)
    dep = Dependency(name="slow", check_cmd=[sys.executable, "-c", "import time; time.sleep(5)"])
    result = checks.fragment_check(_FixedSource([dep]), "linux", False, "").run()
    assert result.state is State.FAIL
    assert "slow" in result.detail


def test_fragment_check_fails_a_malformed_check_cmd():
    """Check that fragment check fails a malformed check cmd."""
    dep = Dependency(name="broken", check_cmd=42)
    result = checks.fragment_check(_FixedSource([dep]), "linux", False, "").run()
    assert result.state is State.FAIL
    assert "broken" in result.detail


def _sycl(name: str) -> Dependency:
    """Return a toolchain dependency providing the SYCL capability."""
    return Dependency(name=name, provides="sycl-toolchain", owner="sushiruntime")


def test_modules_check_passes_with_nothing_missing():
    """Check that modules check passes with nothing missing."""
    assert checks.modules_check((), "sb setup").run().state is State.OK


def test_modules_check_fails_and_names_each_missing_module():
    """Check that modules check fails and names each missing module."""
    result = checks.modules_check((("sushiruntime", "sushiblas"),), "clone it").run()
    assert result.state is State.FAIL
    assert "sushiruntime (wanted by sushiblas)" in result.detail
    assert result.fix == "clone it"


def test_capability_check_fails_for_an_unsatisfied_group():
    """Check that capability check fails for an unsatisfied group."""
    source = _FixedSource([_sycl("intel-llvm"), _sycl("adaptivecpp")])
    result = checks.capability_check(source, {}, "sr setup").run()
    assert result.state is State.FAIL
    assert "sycl-toolchain: none of intel-llvm, adaptivecpp" in result.detail


def test_capability_check_passes_when_one_member_is_present():
    """Check that capability check passes when one member is present."""
    source = _FixedSource([_sycl("intel-llvm"), _sycl("adaptivecpp")])
    result = checks.capability_check(source, {"adaptivecpp": True}, "sr setup").run()
    assert result.state is State.OK
    assert "adaptivecpp" in result.detail


def test_capability_check_passes_when_nothing_is_required():
    """Check that capability check passes when nothing is required."""
    result = checks.capability_check(_FixedSource([]), {}, "sd setup").run()
    assert (result.state, result.detail) == (State.OK, "no toolchain required")


def test_capability_check_names_a_lone_toolchain_once():
    """Check that capability check names a lone toolchain once."""
    source = _FixedSource([Dependency(name="intel-llvm", owner="sushidsp")])
    assert checks.capability_check(source, {"intel-llvm": True}, "sd setup").run().detail == (
        "intel-llvm")
    assert checks.capability_check(source, {}, "sd setup").run().detail == (
        "intel-llvm is not installed")


def test_capability_check_ignores_an_optional_toolchain():
    """Check that capability check ignores an optional toolchain."""
    source = _FixedSource([Dependency(name="intel-llvm", required=False, owner="sushidsp")])
    result = checks.capability_check(source, {}, "sd setup").run()
    assert (result.state, result.detail) == (State.OK, "no toolchain required")
