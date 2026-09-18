"""Keeping a debugging session's device choice out of the cached build environment."""

import json
from pathlib import Path

from sushicore.build_env import (RUNTIME_DEVICE_VARS, merge_env, parse_windows_set,
                                 read_cache, without_device_selection, write_cache)


def _cache(tmp_path: Path, env: dict[str, str], key: str = "k") -> Path:
    cache_file = tmp_path / ".sushi_env.json"
    cache_file.write_text(json.dumps({"key": key, "env": env}))
    return cache_file


def test_without_device_selection_drops_every_listed_variable():
    env = {name: "whatever" for name in RUNTIME_DEVICE_VARS}
    assert without_device_selection(env) == {}


def test_without_device_selection_keeps_the_toolchain_entries():
    env = {"PATH": "C:/msvc/bin", "INCLUDE": "C:/sdk", "ONEAPI_DEVICE_SELECTOR": "opencl:cpu"}
    assert without_device_selection(env) == {"PATH": "C:/msvc/bin", "INCLUDE": "C:/sdk"}


def test_without_device_selection_ignores_case():
    assert without_device_selection({"oneapi_device_selector": "opencl:cpu"}) == {}


def test_a_dumped_shell_environment_loses_only_the_device_choice():
    dumped = parse_windows_set("PATH=C:/msvc/bin\nONEAPI_DEVICE_SELECTOR=opencl:cpu\n")
    assert dumped["ONEAPI_DEVICE_SELECTOR"] == "opencl:cpu"
    assert without_device_selection(dumped) == {"PATH": "C:/msvc/bin"}


def test_a_cache_written_before_this_existed_heals_on_read(tmp_path):
    # The defect this guards: a snapshot taken while a session had pinned SYCL
    # to the CPU kept pinning every later build and run, from any terminal,
    # because the cache is merged over the current environment.
    cache_file = _cache(tmp_path, {"PATH": "C:/msvc/bin", "ONEAPI_DEVICE_SELECTOR": "opencl:cpu"})
    cached = read_cache(cache_file, "k")
    assert cached == {"PATH": "C:/msvc/bin"}

    merged = merge_env({"PATH": "C:/system"}, cached)
    assert "ONEAPI_DEVICE_SELECTOR" not in merged


def test_a_cache_still_round_trips_what_the_build_needs(tmp_path):
    cache_file = tmp_path / ".sushi_env.json"
    write_cache(cache_file, "k", {"PATH": "C:/msvc/bin", "LIB": "C:/msvc/lib"})
    assert read_cache(cache_file, "k") == {"PATH": "C:/msvc/bin", "LIB": "C:/msvc/lib"}


def test_the_current_environment_still_reaches_a_subprocess(tmp_path):
    # Dropping the variable from the snapshot must not stop a caller setting it
    # for one run: merge_env starts from the live environment, so a deliberate
    # export still arrives.
    cached = read_cache(_cache(tmp_path, {"PATH": "C:/msvc/bin"}), "k")
    merged = merge_env({"ONEAPI_DEVICE_SELECTOR": "cuda:gpu", "PATH": "C:/system"}, cached)
    assert merged["ONEAPI_DEVICE_SELECTOR"] == "cuda:gpu"
