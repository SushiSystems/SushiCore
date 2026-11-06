# test_build_admission.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""A tree is put behind the gate by its launcher entries, and refused while the gate is stopped."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore import build_admission, build_gate

K_TREE = Path("trees") / "default-debug"


@pytest.mark.small
def test_the_launcher_runs_the_gate_script_with_the_trees_state_folder():
    defines = build_admission.launcher_defines(K_TREE)
    assert [d.split("=")[0] for d in defines] == ["CMAKE_CXX_COMPILER_LAUNCHER",
                                                  "CMAKE_CXX_LINKER_LAUNCHER"]
    parts = defines[0].split("=", 1)[1].split(";")
    assert Path(parts[2]) == build_admission.gate_script() and parts[2].endswith("build_gate.py")
    assert parts[3] == build_admission.state_dir(K_TREE).as_posix() and parts[4] == "--"


@pytest.mark.small
def test_the_stop_file_is_the_gates_stop_name_under_the_state_folder():
    """Checks the CLI side and the gate name one stop file."""
    assert build_admission.stop_file(K_TREE) == build_admission.state_dir(K_TREE) / build_gate.K_STOP


@pytest.mark.medium
def test_a_build_is_refused_while_the_gate_is_stopped(tmp_path):
    build_dir = tmp_path / "default-debug"
    stop = build_admission.stop_file(build_dir)
    stop.parent.mkdir(parents=True)
    stop.touch()
    with pytest.raises(build_admission.BuildStoppedError):
        build_admission.refuse_a_stopped_gate(build_dir)


@pytest.mark.small
def test_the_launcher_names_the_cache_only_when_there_is_one():
    plain = build_admission.launcher_defines(K_TREE)[0]
    cached = build_admission.launcher_defines(K_TREE, "C:/tools/ccache.exe")[0]
    assert "--cache" not in plain
    assert cached.endswith(";--cache;C:/tools/ccache.exe;--")


@pytest.mark.medium
def test_a_configured_cache_that_is_missing_is_not_used(tmp_path):
    assert build_admission.compiler_cache(str(tmp_path / "missing.exe")) == ""
    present = tmp_path / "ccache.exe"
    present.touch()
    assert build_admission.compiler_cache(str(present)) == str(present)


@pytest.mark.medium
def test_time_trace_requests_are_written_as_the_gate_keys_a_unit(tmp_path):
    build_dir = tmp_path / "default-debug"
    path = build_admission.request_time_traces(build_dir, [r"D:\Src\A.cpp", "b/C.cpp"])
    assert path.name == build_gate.K_TIME_TRACE == build_admission.K_TIME_TRACE_FILE
    assert path.read_text(encoding="utf-8") == "d:/src/a.cpp\nb/c.cpp\n"


@pytest.mark.medium
def test_clearing_time_trace_requests_removes_the_file_and_tolerates_none(tmp_path):
    build_dir = tmp_path / "default-debug"
    path = build_admission.request_time_traces(build_dir, ["a.cpp"])
    build_admission.clear_time_traces(build_dir)
    build_admission.clear_time_traces(build_dir)
    assert not path.exists()
