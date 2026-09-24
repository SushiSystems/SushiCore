# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tests for the doctor framework."""

from __future__ import annotations

from sushicore.provision.doctor import CheckResult, Doctor, FunctionCheck, State


def _check(name, group, required, state, fix=""):
    """Check that check."""
    return FunctionCheck(name, group, required, lambda: CheckResult(state, name, fix))


def test_required_failure_sets_exit_code_one():
    """Check that required failure sets exit code one."""
    report = Doctor([_check("cmake", "build", True, State.FAIL)]).run()
    assert report.failures() == 1
    assert report.exit_code() == 1


def test_optional_failure_only_warns():
    """Check that optional failure only warns."""
    report = Doctor([_check("docker", "build", False, State.FAIL)]).run()
    assert report.exit_code() == 0


def test_group_filter_runs_only_that_group():
    """Check that group filter runs only that group."""
    report = Doctor([_check("cmake", "build", True, State.OK),
                     _check("torch", "infer", True, State.FAIL)]).run(groups={"build"})
    assert [c.name for c, _ in report.rows] == ["cmake"]
    assert report.exit_code() == 0


def test_a_raising_check_is_a_failure_and_the_rest_still_run():
    """Check that a raising check is a failure and the rest still run."""
    def boom():
        """Check that boom."""
        raise OSError("disk gone")
    report = Doctor([FunctionCheck("x", "build", True, boom),
                     _check("y", "build", True, State.OK)]).run()
    states = [(c.name, r.state) for c, r in report.rows]
    assert states == [("x", State.FAIL), ("y", State.OK)]
    assert "disk gone" in report.rows[0][1].detail


def test_render_prints_a_table_and_a_result(recording_console):
    """Check that render prints a table and a result."""
    doctor = Doctor([_check("cmake", "build", True, State.OK, fix="st setup")])
    doctor.render(doctor.run(), recording_console)
    methods = [m for m, _ in recording_console.calls]
    assert methods == ["table", "result"]


def test_json_state_matches_the_table_for_a_non_required_failure(recording_console):
    """Check that json state matches the table for a non required failure."""
    doctor = Doctor([_check("docker", "build", False, State.FAIL)])
    doctor.render(doctor.run(), recording_console)
    table_rows = next(args[1] for name, args in recording_console.calls if name == "table")
    payload = next(args[1] for name, args in recording_console.calls if name == "result")
    assert "warn" in table_rows[0][2]
    assert payload["checks"][0]["state"] == "warn"


def test_optional_failure_in_a_plain_run_warns_and_exits_zero(recording_console):
    doctor = Doctor([_check("torch", "infer", False, State.FAIL)])
    report = doctor.run()
    doctor.render(report, recording_console)
    payload = next(args[1] for name, args in recording_console.calls if name == "result")
    assert report.exit_code() == 0
    assert payload["checks"][0]["state"] == "warn"
    assert payload["checks"][0]["required"] is False


def test_optional_failure_in_a_named_group_fails_and_exits_one(recording_console):
    doctor = Doctor([_check("torch", "infer", False, State.FAIL),
                     _check("cmake", "build", True, State.FAIL)])
    report = doctor.run({"infer"})
    doctor.render(report, recording_console)
    table_rows = next(args[1] for name, args in recording_console.calls if name == "table")
    payload = next(args[1] for name, args in recording_console.calls if name == "result")
    assert [c.name for c, _ in report.rows] == ["torch"]
    assert report.failures() == 1
    assert report.exit_code() == 1
    assert "FAIL" in table_rows[0][2]
    assert payload["checks"][0]["state"] == "fail"
    assert payload["checks"][0]["required"] is True


def test_required_failure_is_unaffected_by_the_group_filter():
    doctor = Doctor([_check("torch", "infer", True, State.FAIL)])
    assert doctor.run().exit_code() == 1
    assert doctor.run({"infer"}).exit_code() == 1
