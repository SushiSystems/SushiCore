# test_build_admission.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""A tree is put behind the gate by its launcher entries, and refused while the gate is stopped."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore import build_admission, build_gate

pytestmark = pytest.mark.small


def test_the_launcher_runs_the_gate_script_with_the_trees_state_folder(tmp_path):
    defines = build_admission.launcher_defines(tmp_path)
    assert [d.split("=")[0] for d in defines] == ["CMAKE_CXX_COMPILER_LAUNCHER",
                                                  "CMAKE_CXX_LINKER_LAUNCHER"]
    parts = defines[0].split("=", 1)[1].split(";")
    assert Path(parts[2]) == build_admission.gate_script() and parts[2].endswith("build_gate.py")
    assert parts[3] == build_admission.state_dir(tmp_path).as_posix() and parts[4] == "--"
    assert build_admission.gate_script().is_file()


def test_a_build_is_refused_while_the_gate_is_stopped(tmp_path):
    """Checks the CLI side and the gate name one stop file, and a build does not start beside it."""
    build_dir = tmp_path / "default-debug"
    stop = build_admission.stop_file(build_dir)
    assert stop == build_admission.state_dir(build_dir) / build_gate.K_STOP
    build_admission.refuse_a_stopped_gate(build_dir)
    stop.parent.mkdir(parents=True)
    stop.touch()
    with pytest.raises(build_admission.BuildStoppedError):
        build_admission.refuse_a_stopped_gate(build_dir)


def test_the_launcher_names_the_cache_only_when_there_is_one(tmp_path):
    plain = build_admission.launcher_defines(tmp_path)[0]
    cached = build_admission.launcher_defines(tmp_path, "C:/tools/ccache.exe")[0]
    assert "--cache" not in plain
    assert cached.endswith(";--cache;C:/tools/ccache.exe;--")


def test_a_configured_cache_that_is_missing_is_not_used(tmp_path):
    assert build_admission.compiler_cache(str(tmp_path / "missing.exe")) == ""
    present = tmp_path / "ccache.exe"
    present.touch()
    assert build_admission.compiler_cache(str(present)) == str(present)
