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


class _Console:
    def __init__(self):
        self.lines = []

    def info(self, text):
        self.lines.append(("info", text))

    def warn(self, text):
        self.lines.append(("warn", text))


def _fake_run(monkeypatch, code, stdout):
    import subprocess
    from types import SimpleNamespace
    seen = []

    def _run(script, **kw):
        seen.append(script)
        return SimpleNamespace(returncode=code, stdout=stdout)

    monkeypatch.setattr(subprocess, "run", _run)
    return seen


def test_snapshot_vcvars_names_the_path_and_drops_device_selection(monkeypatch):
    from sushicore.build_env import snapshot_vcvars
    seen = _fake_run(monkeypatch, 0, "PATH=C:/msvc\nCUDA_VISIBLE_DEVICES=0\n")
    console = _Console()
    vcvars = Path("C:/VS/vcvars64.bat")
    assert snapshot_vcvars(vcvars, console) == {"PATH": "C:/msvc"}
    assert seen == [f'cmd /c call "{vcvars}" >nul && set']
    assert console.lines == [("info", f"Loading Visual Studio environment from {vcvars}")]


def test_snapshot_vcvars_warns_and_returns_none_on_failure(monkeypatch):
    from sushicore.build_env import snapshot_vcvars
    _fake_run(monkeypatch, 1, "")
    console = _Console()
    assert snapshot_vcvars(Path("C:/VS/vcvars64.bat"), console) is None
    assert console.lines[-1] == ("warn", "vcvars64.bat returned non-zero; using the current env.")


def test_snapshot_windows_keeps_its_own_command_and_messages(monkeypatch, tmp_path):
    from types import SimpleNamespace
    from sushicore.build_env import snapshot_windows
    vcvars = tmp_path / "vcvars64.bat"
    vcvars.write_text("")
    seen = _fake_run(monkeypatch, 0, "PATH=C:/msvc\n")
    console = _Console()
    cfg = SimpleNamespace(vs_vcvars=str(vcvars), expand=lambda s: s)
    assert snapshot_windows(cfg, console) == {"PATH": "C:/msvc"}
    assert seen == ['cmd /c call "' + str(vcvars) + '" && set']
    assert console.lines == [("info", "Loading Visual Studio environment (vcvars64)...")]
