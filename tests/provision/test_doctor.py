# test_doctor.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests for the doctor framework."""

from __future__ import annotations

import pytest

from sushicore.console_memory import RecordingConsole
from sushicore.provision.doctor import CheckResult, Doctor, FunctionCheck, State


def _check(name, group, required, state, fix=""):
    """Check that check."""
    return FunctionCheck(name, group, required, lambda: CheckResult(state, name, fix))


@pytest.mark.small
def test_required_failure_sets_exit_code_one():
    """Check that required failure sets exit code one."""
    report = Doctor([_check("cmake", "build", True, State.FAIL)]).run()
    assert report.failures() == 1
    assert report.exit_code() == 1


@pytest.mark.small
def test_optional_failure_only_warns():
    """Check that optional failure only warns."""
    report = Doctor([_check("docker", "build", False, State.FAIL)]).run()
    assert report.exit_code() == 0


@pytest.mark.small
def test_group_filter_runs_only_that_group():
    """Check that group filter runs only that group."""
    report = Doctor([_check("cmake", "build", True, State.OK),
                     _check("torch", "infer", True, State.FAIL)]).run(groups={"build"})
    assert [c.name for c, _ in report.rows] == ["cmake"]
    assert report.exit_code() == 0


def _raising(check_name):
    """Return a check named *check_name* whose function raises."""
    def boom():
        """Raise as a check that cannot reach its resource does."""
        raise OSError("disk gone")
    return FunctionCheck(check_name, "build", True, boom)


@pytest.mark.small
def test_a_raising_check_is_a_failure():
    """Check that a check that raises is reported as a failure carrying the error text."""
    report = Doctor([_raising("x")]).run()
    assert report.rows[0][1].state is State.FAIL
    assert "disk gone" in report.rows[0][1].detail


@pytest.mark.small
def test_the_checks_after_a_raising_check_still_run():
    """Check that a check after a raising one still runs."""
    report = Doctor([_raising("x"), _check("y", "build", True, State.OK)]).run()
    assert [(c.name, r.state) for c, r in report.rows][1] == ("y", State.OK)


@pytest.mark.small
def test_render_prints_a_table_and_a_result():
    """Check that render prints a table and then a result."""
    console = RecordingConsole()
    doctor = Doctor([_check("cmake", "build", True, State.OK, fix="st setup")])
    doctor.render(doctor.run(), console)
    assert [m for m, _ in console.calls] == ["table", "result"]


@pytest.mark.small
def test_an_optional_failure_in_a_plain_run_warns_in_table_and_payload_and_exits_zero():
    """Check that the table row, the payload and the exit code agree on an optional failure."""
    console = RecordingConsole()
    doctor = Doctor([_check("torch", "infer", False, State.FAIL)])
    report = doctor.run()
    doctor.render(report, console)
    table_rows = next(args[1] for name, args in console.calls if name == "table")
    payload = next(args[1] for name, args in console.calls if name == "result")
    assert "warn" in table_rows[0][2]
    assert (payload["checks"][0]["state"], payload["checks"][0]["required"]) == ("warn", False)
    assert report.exit_code() == 0


@pytest.mark.small
def test_an_optional_failure_in_a_named_group_exits_one():
    """Check that an optional failure counts as a failure when its group is named."""
    doctor = Doctor([_check("torch", "infer", False, State.FAIL),
                     _check("cmake", "build", True, State.FAIL)])
    report = doctor.run({"infer"})
    assert ([c.name for c, _ in report.rows], report.failures(), report.exit_code()) == (
        ["torch"], 1, 1)


@pytest.mark.small
def test_an_optional_failure_in_a_named_group_fails_in_table_and_payload():
    """Check that the table and the payload both say fail for an optional failure in its group."""
    console = RecordingConsole()
    doctor = Doctor([_check("torch", "infer", False, State.FAIL)])
    doctor.render(doctor.run({"infer"}), console)
    table_rows = next(args[1] for name, args in console.calls if name == "table")
    payload = next(args[1] for name, args in console.calls if name == "result")
    assert "FAIL" in table_rows[0][2]
    assert (payload["checks"][0]["state"], payload["checks"][0]["required"]) == ("fail", True)


@pytest.mark.small
def test_required_failure_is_unaffected_by_the_group_filter():
    """Check that a required failure exits one with or without the group filter."""
    doctor = Doctor([_check("torch", "infer", True, State.FAIL)])
    assert (doctor.run().exit_code(), doctor.run({"infer"}).exit_code()) == (1, 1)
