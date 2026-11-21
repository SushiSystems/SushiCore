# test_unit_peaks.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""A unit keeps the peak it was last measured at, and a kind reads its largest from its units."""

from __future__ import annotations

import pytest

from sushicore.unit_peaks import UnitPeaks


def _table(*entries: tuple[str, str, int]) -> UnitPeaks:
    """Return a table in which each (kind, key, peak) was measured exactly once."""
    table = UnitPeaks()
    for kind, key, peak in entries:
        table.record(kind, key, peak, exact=True)
    return table


@pytest.mark.small
def test_an_exact_measurement_replaces_a_heavier_one():
    table = _table(("device_compile", "a.cpp", 9400))
    table.record("device_compile", "a.cpp", 2800, exact=True)
    assert table.peak_of("a.cpp") == 2800


@pytest.mark.small
def test_a_measurement_the_cache_may_have_answered_never_lowers_a_peak():
    table = _table(("host_compile", "a.cpp", 800))
    table.record("host_compile", "a.cpp", 20, exact=False)
    assert table.peak_of("a.cpp") == 800


@pytest.mark.small
def test_a_measurement_the_cache_may_have_answered_raises_a_peak():
    table = _table(("host_compile", "a.cpp", 800))
    table.record("host_compile", "a.cpp", 900, exact=False)
    assert table.peak_of("a.cpp") == 900


@pytest.mark.small
def test_a_kinds_largest_peak_falls_when_its_heaviest_unit_grows_lighter():
    table = _table(("device_compile", "a.cpp", 9400), ("device_compile", "b.cpp", 1200))
    table.record("device_compile", "a.cpp", 1000, exact=True)
    assert table.largest("device_compile") == 1200


@pytest.mark.small
def test_a_unit_that_changes_kind_leaves_its_old_kind():
    table = _table(("device_compile", "a.cpp", 9400))
    table.record("host_compile", "a.cpp", 300, exact=False)
    assert (table.largest("device_compile"), table.count("device_compile")) == (0, 0)


@pytest.mark.small
def test_a_kind_counts_each_of_its_units_once():
    table = _table(("host_compile", "a.cpp", 300), ("host_compile", "a.cpp", 500),
                   ("host_compile", "b.cpp", 200), ("device_compile", "c.cpp", 900))
    assert table.count("host_compile") == 2


@pytest.mark.small
def test_a_unit_never_measured_has_no_peak():
    assert UnitPeaks().peak_of("a.cpp") is None


@pytest.mark.small
def test_the_heaviest_units_come_first_up_to_the_limit():
    table = _table(("host_compile", "a.cpp", 300), ("device_compile", "b.cpp", 900),
                   ("host_compile", "c.cpp", 500))
    assert table.heaviest(2) == [(900, "b.cpp"), (500, "c.cpp")]


@pytest.mark.small
def test_a_table_reads_back_as_it_was_written():
    table = _table(("host_compile", "a.cpp", 300), ("device_compile", "b.cpp", 900))
    again = UnitPeaks.from_json(table.to_json())
    assert (again.heaviest(5), again.kinds()) == (table.heaviest(5), {"host_compile", "device_compile"})


@pytest.mark.small
@pytest.mark.parametrize("data", [
    {"a.cpp": 9400, "@device_compile": 9367, "#device_compile": 21},
    [],
    {"units": {"a.cpp": {"kind": "host_compile", "peak": "many"}}},
])
def test_data_of_another_form_reads_as_no_unit(data):
    assert UnitPeaks.from_json(data).heaviest(5) == []
