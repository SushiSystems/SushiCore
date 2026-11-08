# test_checks.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the stock doctor checks."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from sushicore.provision import checks
from sushicore.provision.doctor import State
from sushicore.provision.fragments import Dependency
from sushicore.provision.fragments_memory import InMemoryDependencySource


K_MISSING = Path("/machine/nope")
K_PRESENT = Path("/machine/yolox")


def _packaged(name: str, **fields) -> Dependency:
    """Return a dependency with an apt package, so a Linux selection holds it."""
    return Dependency(name=name, linux_apt=[name], **fields)


def _sycl(name: str) -> Dependency:
    """Return a toolchain dependency providing the SYCL capability."""
    return Dependency(name=name, provides="sycl-toolchain", owner="sushiruntime")


def _timing_out(command):
    """Raise as a command that outlives its timeout does."""
    raise subprocess.TimeoutExpired(command, 0.1)


def _malformed(command):
    """Raise as a command of the wrong type does."""
    raise TypeError(command)


@pytest.mark.small
def test_python_check_passes_when_the_version_meets_the_minimum():
    """Check that python check passes and names the interpreter when the version is enough."""
    result = checks.python_check((3, 10), version=(3, 11), executable="/py/python").run()
    assert (result.state, result.detail) == (State.OK, "/py/python (Python 3.11)")


@pytest.mark.small
def test_python_check_fails_with_the_fix_when_the_version_is_too_old():
    """Check that python check fails and names the minimum to install when the version is older."""
    result = checks.python_check((3, 10), version=(3, 8), executable="/py/python").run()
    assert (result.state, result.fix) == (State.FAIL, "install Python 3.10+")


@pytest.mark.small
def test_tool_check_fails_with_the_fix_for_a_missing_tool():
    """Check that tool check fails with the fix for a tool that does not run."""
    result = checks.tool_check("x", "no-such-tool", fix="st setup", works=lambda exe: False).run()
    assert (result.state, result.fix) == (State.FAIL, "st setup")


@pytest.mark.small
def test_python_module_check_passes_when_the_finder_gives_a_spec():
    """Check that python module check passes when the finder gives a spec."""
    result = checks.python_module_check("json", "eval", True, "",
                                        finder=lambda name: object()).run()
    assert result.state is State.OK


@pytest.mark.small
def test_missing_python_module_fails():
    """Check that python module check fails with the fix when the finder gives no spec."""
    result = checks.python_module_check("sushi_no_such_mod", "infer", True, "pip install x",
                                        finder=lambda name: None).run()
    assert (result.state, result.fix) == (State.FAIL, "pip install x")


@pytest.mark.small
def test_path_check_reports_the_missing_path():
    """Check that path check fails and names the path when it does not exist."""
    result = checks.path_check("yolox", K_MISSING, "infer", True, "git submodule update",
                               exists=lambda path: False).run()
    assert result.state is State.FAIL and "nope" in result.detail


@pytest.mark.small
def test_path_check_passes_on_a_present_path():
    """Check that path check passes and names the path when it exists."""
    result = checks.path_check("yolox", K_PRESENT, "infer", True, "git submodule update",
                               exists=lambda path: True).run()
    assert (result.state, result.detail) == (State.OK, str(K_PRESENT))


@pytest.mark.small
def test_stamp_check_warns_on_an_unstamped_toolchain():
    """Check that stamp check warns and names a toolchain folder that holds no stamp."""
    result = checks.stamp_check(Path("/root"), stamps=lambda folder: {"llvm-sycl": False}).run()
    assert result.state is State.WARN and "llvm-sycl" in result.detail


@pytest.mark.small
def test_stamp_check_passes_when_every_toolchain_is_stamped():
    """Check that stamp check passes when each toolchain folder holds its stamp."""
    result = checks.stamp_check(Path("/root"), stamps=lambda folder: {"llvm-sycl": True}).run()
    assert result.state is State.OK


@pytest.mark.small
def test_stamp_check_passes_with_no_toolchain_installed():
    """Check that stamp check passes when no toolchains folder exists."""
    assert checks.stamp_check(Path("/root"), stamps=lambda folder: None).run().state is State.OK


@pytest.mark.small
def test_stamp_check_warns_when_the_toolchains_folder_cannot_be_read():
    """Check that stamp check warns and says so when the toolchains folder cannot be listed."""
    def refuse(folder):
        raise PermissionError("denied")

    result = checks.stamp_check(Path("/root"), stamps=refuse).run()
    assert result.state is State.WARN and "cannot read" in result.detail


@pytest.mark.small
def test_fragment_check_passes_a_dependency_whose_check_cmd_succeeds():
    """Check that fragment check passes when every check cmd exits zero."""
    source = InMemoryDependencySource([_packaged("python", check_cmd=["python", "-V"])])
    result = checks.fragment_check(source, "linux", False, "", succeeds=lambda cmd: True).run()
    assert result.state is State.OK


@pytest.mark.small
def test_fragment_check_fails_a_dependency_whose_check_cmd_exits_non_zero():
    """Check that fragment check fails a required dependency whose check cmd exits non-zero."""
    source = InMemoryDependencySource([_packaged("python", check_cmd=["python", "-V"])])
    result = checks.fragment_check(source, "linux", False, "", succeeds=lambda cmd: False).run()
    assert result.state is State.FAIL


@pytest.mark.small
def test_fragment_check_fails_a_dependency_whose_check_cmd_hangs():
    """Check that fragment check fails a dependency whose check cmd outlives its timeout."""
    source = InMemoryDependencySource([_packaged("slow", check_cmd=["sleep", "5"])])
    result = checks.fragment_check(source, "linux", False, "", succeeds=_timing_out).run()
    assert result.state is State.FAIL
    assert "slow" in result.detail


@pytest.mark.small
def test_fragment_check_fails_a_malformed_check_cmd():
    """Check that fragment check fails a dependency whose check cmd is not a command."""
    source = InMemoryDependencySource([_packaged("broken", check_cmd=["x"])])
    result = checks.fragment_check(source, "linux", False, "", succeeds=_malformed).run()
    assert result.state is State.FAIL
    assert "broken" in result.detail


@pytest.mark.small
def test_modules_check_passes_with_nothing_missing():
    """Check that modules check passes with nothing missing."""
    assert checks.modules_check((), "sb setup").run().state is State.OK


@pytest.mark.small
def test_modules_check_fails_and_names_each_missing_module():
    """Check that modules check fails and names each missing module."""
    result = checks.modules_check((("sushiruntime", "sushiblas"),), "clone it").run()
    assert result.state is State.FAIL
    assert "sushiruntime (wanted by sushiblas)" in result.detail
    assert result.fix == "clone it"


@pytest.mark.small
def test_capability_check_fails_for_an_unsatisfied_group():
    """Check that capability check fails for a group none of whose members is present."""
    source = InMemoryDependencySource([_sycl("intel-llvm"), _sycl("adaptivecpp")])
    result = checks.capability_check(source, {}, "sr setup").run()
    assert result.state is State.FAIL
    assert "sycl-toolchain: none of intel-llvm, adaptivecpp" in result.detail


@pytest.mark.small
def test_capability_check_passes_when_one_member_is_present():
    """Check that capability check passes and names the member that is present."""
    source = InMemoryDependencySource([_sycl("intel-llvm"), _sycl("adaptivecpp")])
    result = checks.capability_check(source, {"adaptivecpp": True}, "sr setup").run()
    assert result.state is State.OK
    assert "adaptivecpp" in result.detail


@pytest.mark.small
def test_capability_check_passes_when_nothing_is_required():
    """Check that capability check passes when no toolchain is required."""
    result = checks.capability_check(InMemoryDependencySource([]), {}, "sd setup").run()
    assert (result.state, result.detail) == (State.OK, "no toolchain required")


@pytest.mark.small
def test_capability_check_names_a_present_lone_toolchain_once():
    """Check that capability check names a lone toolchain that is present by its name alone."""
    source = InMemoryDependencySource([Dependency(name="intel-llvm", owner="sushidsp")])
    assert checks.capability_check(source, {"intel-llvm": True}, "sd setup").run().detail == (
        "intel-llvm")


@pytest.mark.small
def test_capability_check_names_a_missing_lone_toolchain_once():
    """Check that capability check says a lone toolchain that is absent is not installed."""
    source = InMemoryDependencySource([Dependency(name="intel-llvm", owner="sushidsp")])
    assert checks.capability_check(source, {}, "sd setup").run().detail == (
        "intel-llvm is not installed")


@pytest.mark.small
def test_capability_check_ignores_an_optional_toolchain():
    """Check that capability check requires nothing of an optional toolchain."""
    source = InMemoryDependencySource(
        [Dependency(name="intel-llvm", required=False, owner="sushidsp")])
    result = checks.capability_check(source, {}, "sd setup").run()
    assert (result.state, result.detail) == (State.OK, "no toolchain required")


@pytest.mark.small
def test_fragment_check_passes_a_dependency_the_package_manager_reports():
    """Check that a failing check cmd is overruled by a package manager holding the package."""
    source = InMemoryDependencySource([_packaged("hwloc", check_cmd=["no-such-tool"])])
    result = checks.fragment_check(source, "linux", False, "", installed=lambda dep: True,
                                   succeeds=lambda cmd: False).run()
    assert result.state is State.OK


@pytest.mark.small
def test_fragment_check_fails_a_dependency_no_package_manager_reports():
    """Check that a failing check cmd stands when no package manager holds the package."""
    source = InMemoryDependencySource([_packaged("hwloc", check_cmd=["no-such-tool"])])
    result = checks.fragment_check(source, "linux", False, "", installed=lambda dep: False,
                                   succeeds=lambda cmd: False).run()
    assert result.state is State.FAIL
    assert "hwloc" in result.detail


@pytest.mark.small
@pytest.mark.parametrize("name", ["cmake", "ninja", "doxygen", "git", "intel-llvm"])
def test_digest_check_warns_and_names_each_unpinned_download(name):
    """Check that doctor names each download this platform would fetch unverified."""
    source = InMemoryDependencySource([Dependency(name="intel-llvm")])
    result = checks.digest_check(source, "windows").run()
    assert result.state is State.WARN and name in result.detail


@pytest.mark.small
def test_digest_check_leaves_oneapi_out_of_the_unpinned_names():
    """Check that doctor does not name oneapi, which no fragment declares."""
    source = InMemoryDependencySource([Dependency(name="intel-llvm")])
    assert "oneapi" not in checks.digest_check(source, "windows").run().detail


@pytest.mark.small
def test_digest_check_tells_how_to_pin():
    """Check that the unpinned warning tells the maintainer to pin a sha256."""
    source = InMemoryDependencySource([Dependency(name="intel-llvm")])
    assert "sha256" in checks.digest_check(source, "windows").run().fix


@pytest.mark.small
def test_digest_check_is_not_required():
    """Check that an unpinned download warns without being a required check."""
    source = InMemoryDependencySource([Dependency(name="intel-llvm")])
    assert checks.digest_check(source, "windows").required is False


@pytest.mark.small
def test_digest_check_passes_when_every_download_is_pinned():
    """Check that doctor reports nothing to pin once each download carries a digest."""
    pin = {"windows": "3f" * 32}
    names = ("cmake", "ninja", "doxygen", "git", "intel-llvm")
    source = InMemoryDependencySource([Dependency(name=name, sha256=pin) for name in names])

    assert checks.digest_check(source, "windows").run().state is State.OK


@pytest.mark.small
def test_digest_check_passes_where_nothing_is_downloaded():
    """Check that a platform fetching nothing directly has nothing unpinned."""
    source = InMemoryDependencySource([Dependency(name="hwloc")])

    assert checks.digest_check(source, "linux").run().state is State.OK
