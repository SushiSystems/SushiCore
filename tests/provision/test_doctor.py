# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the doctor framework."""

from __future__ import annotations

from sushicore.provision.doctor import CheckResult, Doctor, FunctionCheck, State


def _check(name, group, required, state, fix=""):
    return FunctionCheck(name, group, required, lambda: CheckResult(state, name, fix))


def test_required_failure_sets_exit_code_one():
    report = Doctor([_check("cmake", "build", True, State.FAIL)]).run()
    assert report.failures() == 1
    assert report.exit_code() == 1


def test_optional_failure_only_warns():
    report = Doctor([_check("docker", "build", False, State.FAIL)]).run()
    assert report.exit_code() == 0


def test_group_filter_runs_only_that_group():
    report = Doctor([_check("cmake", "build", True, State.OK),
                     _check("torch", "infer", True, State.FAIL)]).run(groups={"build"})
    assert [c.name for c, _ in report.rows] == ["cmake"]
    assert report.exit_code() == 0


def test_a_raising_check_is_a_failure_and_the_rest_still_run():
    def boom():
        raise OSError("disk gone")
    report = Doctor([FunctionCheck("x", "build", True, boom),
                     _check("y", "build", True, State.OK)]).run()
    states = [(c.name, r.state) for c, r in report.rows]
    assert states == [("x", State.FAIL), ("y", State.OK)]
    assert "disk gone" in report.rows[0][1].detail


def test_render_prints_a_table_and_a_result(recording_console):
    doctor = Doctor([_check("cmake", "build", True, State.OK, fix="st setup")])
    doctor.render(doctor.run(), recording_console)
    methods = [m for m, _ in recording_console.calls]
    assert methods == ["table", "result"]


def test_json_state_matches_the_table_for_a_non_required_failure(recording_console):
    doctor = Doctor([_check("docker", "build", False, State.FAIL)])
    doctor.render(doctor.run(), recording_console)
    table_rows = next(args[1] for name, args in recording_console.calls if name == "table")
    payload = next(args[1] for name, args in recording_console.calls if name == "result")
    assert "warn" in table_rows[0][2]
    assert payload["checks"][0]["state"] == "warn"
