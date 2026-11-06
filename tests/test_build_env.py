# test_build_env.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Keeping a debugging session's device choice out of the cached build environment."""

import json
import os
import subprocess
from dataclasses import dataclass, replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from sushicore.build_env import (CALLER_TEMP_VARS, RUNTIME_DEVICE_VARS, StackBuildEnv, merge_env,
                                 parse_windows_set, prepend_path, read_cache, snapshot_vcvars,
                                 snapshot_windows, without_caller_choices,
                                 without_device_selection, write_cache)
from sushicore.config_base import ToolConfig
from sushicore.console_memory import RecordingConsole
from sushicore.profile import ModuleProfile


@dataclass
class _SiblingConfig(ToolConfig):
    """A tool config with one sibling checkout, as a module that builds a dependency in-tree has."""

    core_dir: str = ""


K_CONFIG = _SiblingConfig(platform="windows", vs_vcvars="C:/VS/vcvars64.bat", core_dir="D:/core")


def _fake_run(monkeypatch, code, stdout):
    """Replace ``subprocess.run`` with a function that records the script and answers *code*."""
    seen = []

    def _run(script, **kw):
        seen.append(script)
        return SimpleNamespace(returncode=code, stdout=stdout)

    monkeypatch.setattr(subprocess, "run", _run)
    return seen


@pytest.mark.small
def test_without_device_selection_drops_every_listed_variable():
    env = {name: "whatever" for name in RUNTIME_DEVICE_VARS}
    assert without_device_selection(env) == {}


@pytest.mark.small
def test_without_device_selection_keeps_the_toolchain_entries():
    env = {"PATH": "C:/msvc/bin", "INCLUDE": "C:/sdk", "ONEAPI_DEVICE_SELECTOR": "opencl:cpu"}
    assert without_device_selection(env) == {"PATH": "C:/msvc/bin", "INCLUDE": "C:/sdk"}


@pytest.mark.small
def test_without_device_selection_ignores_case():
    assert without_device_selection({"oneapi_device_selector": "opencl:cpu"}) == {}


@pytest.mark.small
def test_a_dumped_shell_environment_loses_only_the_device_choice():
    dumped = parse_windows_set("PATH=C:/msvc/bin\nONEAPI_DEVICE_SELECTOR=opencl:cpu\n")
    assert dumped["ONEAPI_DEVICE_SELECTOR"] == "opencl:cpu"
    assert without_device_selection(dumped) == {"PATH": "C:/msvc/bin"}


@pytest.mark.small
def test_without_caller_choices_drops_the_scratch_folder():
    env = {name: "C:/Users/me/AppData/Local/Temp" for name in CALLER_TEMP_VARS}
    env["PATH"] = "C:/msvc/bin"
    assert without_caller_choices(env) == {"PATH": "C:/msvc/bin"}


@pytest.mark.small
def test_without_caller_choices_drops_the_device_choice():
    env = {"PATH": "C:/msvc/bin", "ONEAPI_DEVICE_SELECTOR": "opencl:cpu"}
    assert without_caller_choices(env) == {"PATH": "C:/msvc/bin"}


@pytest.mark.small
def test_a_callers_scratch_folder_survives_a_cached_snapshot():
    # A snapshot's TMP must not send every compile's temporaries to the drive it was taken on.
    cached = without_caller_choices({"PATH": "C:/msvc/bin", "TMP": "C:/Temp"})
    assert merge_env({"TMP": "D:/build/tmp"}, cached)["TMP"] == "D:/build/tmp"


@pytest.mark.small
def test_a_cache_written_before_this_existed_heals_on_read():
    # A stale cache must not pin the device for later runs; see docs/architecture/OVERVIEW.md.
    cached = without_caller_choices({"PATH": "C:/msvc/bin", "ONEAPI_DEVICE_SELECTOR": "opencl:cpu"})
    merged = merge_env({"PATH": "C:/system"}, cached)
    assert "ONEAPI_DEVICE_SELECTOR" not in merged


@pytest.mark.medium
def test_a_cache_still_round_trips_what_the_build_needs(tmp_path):
    cache_file = tmp_path / ".sushi_env.json"
    write_cache(cache_file, "k", {"PATH": "C:/msvc/bin", "LIB": "C:/msvc/lib"})
    assert read_cache(cache_file, "k") == {"PATH": "C:/msvc/bin", "LIB": "C:/msvc/lib"}


@pytest.mark.small
def test_a_callers_device_choice_survives_the_merge_with_a_cached_snapshot():
    # A caller's own export still reaches the run; see docs/architecture/OVERVIEW.md, build_env.
    merged = merge_env({"ONEAPI_DEVICE_SELECTOR": "cuda:gpu", "PATH": "C:/system"},
                       {"PATH": "C:/msvc/bin"})
    assert merged["ONEAPI_DEVICE_SELECTOR"] == "cuda:gpu"


@pytest.mark.small
def test_snapshot_vcvars_names_the_path_and_drops_device_selection(monkeypatch):
    seen = _fake_run(monkeypatch, 0, "PATH=C:/msvc\nCUDA_VISIBLE_DEVICES=0\n")
    console = RecordingConsole()
    vcvars = Path("C:/VS/vcvars64.bat")
    assert snapshot_vcvars(vcvars, console) == {"PATH": "C:/msvc"}
    assert seen == [f'cmd /c call "{vcvars}" >nul && set']
    assert console.texts("info") == [f"Loading Visual Studio environment from {vcvars}"]


@pytest.mark.small
def test_snapshot_vcvars_warns_and_returns_none_on_failure(monkeypatch):
    _fake_run(monkeypatch, 1, "")
    console = RecordingConsole()
    assert snapshot_vcvars(Path("C:/VS/vcvars64.bat"), console) is None
    assert console.texts("warn") == ["vcvars64.bat returned non-zero; using the current env."]


@pytest.mark.medium
def test_snapshot_windows_keeps_its_own_command_and_messages(monkeypatch, tmp_path):
    vcvars = tmp_path / "vcvars64.bat"
    vcvars.write_text("")
    seen = _fake_run(monkeypatch, 0, "PATH=C:/msvc\n")
    console = RecordingConsole()
    cfg = ToolConfig(vs_vcvars=str(vcvars))
    assert snapshot_windows(cfg, console) == {"PATH": "C:/msvc"}
    assert seen == ['cmd /c call "' + str(vcvars) + '" && set']
    assert console.texts("info") == ["Loading Visual Studio environment (vcvars64)..."]


@pytest.mark.medium
def test_a_cache_that_cannot_be_written_is_recorded(tmp_path, caplog):
    """Check that write_cache logs one warning naming the file it could not write."""
    cache_file = tmp_path / "taken"
    cache_file.mkdir()
    with caplog.at_level("WARNING", logger="sushicore.build_env"):
        write_cache(cache_file, "k", {"PATH": "C:/msvc/bin"})
    warnings = [r for r in caplog.records if r.name == "sushicore.build_env"]
    assert [r.levelname for r in warnings] == ["WARNING"]
    assert str(cache_file) in warnings[0].getMessage()


@pytest.mark.small
def test_prepend_path_puts_the_directories_first_in_a_case_insensitive_variable():
    env = {"Path": "C:/old"}
    prepend_path(env, "PATH", ["C:/a", "C:/b"])
    assert env == {"Path": os.pathsep.join(["C:/a", "C:/b", "C:/old"])}


@pytest.mark.small
@pytest.mark.parametrize("changed", [
    {"platform": "linux"},
    {"vs_vcvars": "C:/VS2/vcvars64.bat"},
    {"core_dir": "D:/elsewhere"},
])
def test_the_cache_key_changes_with_the_platform_the_vcvars_or_a_sibling_directory(changed):
    build_env = StackBuildEnv(profile=ModuleProfile("SushiTest", "st", "ST", siblings=("core",)),
                              console=None, find_root=None)
    assert build_env.cache_key(replace(K_CONFIG, **changed)) != build_env.cache_key(K_CONFIG)


@pytest.mark.small
def test_the_cache_key_does_not_change_with_an_unrelated_setting():
    build_env = StackBuildEnv(profile=ModuleProfile("SushiTest", "st", "ST", siblings=("core",)),
                              console=None, find_root=None)
    assert build_env.cache_key(replace(K_CONFIG, cxx="clang++")) == build_env.cache_key(K_CONFIG)
