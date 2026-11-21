# unit_peaks.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The peak memory each build unit was last measured at, and what its kind shows from them."""

from __future__ import annotations

from typing import final

#: The key of the units in the table's JSON form.
K_UNITS = "units"


@final
class UnitPeaks:
    """Keeps, per unit key, its kind and the peak in megabytes it was last measured at.

    A kind's largest peak and its unit count are read from the units held now, so a unit that grew
    lighter, or a unit that left the kind, stops weighing on the kind as soon as it is measured again.
    The table imports nothing from the package, so `build_gate` can load it by path.
    """

    def __init__(self) -> None:
        """Start with no unit measured."""
        self._units: dict[str, tuple[str, int]] = {}

    @classmethod
    def from_json(cls, data: object) -> UnitPeaks:
        """Return the table *data* holds; an empty one when *data* is not a table of this form.

        A file of another form, such as one written before the kinds were kept per unit, holds no
        unit: its numbers cannot be told apart by kind, and the next build measures them again.
        """
        table = cls()
        units = data.get(K_UNITS) if isinstance(data, dict) else None
        if not isinstance(units, dict):
            return table
        for key, entry in units.items():
            if isinstance(entry, dict) and isinstance(entry.get("kind"), str) \
                    and isinstance(entry.get("peak"), int):
                table._units[key] = (entry["kind"], entry["peak"])
        return table

    def to_json(self) -> dict:
        """Return the table as the JSON object `from_json` reads back."""
        return {K_UNITS: {key: {"kind": kind, "peak": peak}
                          for key, (kind, peak) in self._units.items()}}

    def record(self, kind: str, key: str, peak: int, *, exact: bool) -> None:
        """Record that the unit *key* of *kind* peaked at *peak*.

        An exact measurement, one the compiler ran for in full, replaces the unit's peak. One that
        may have been answered by a cache only raises it: a cache hit costs almost nothing and says
        nothing about what the next real compile needs.
        """
        previous = self._units.get(key)
        if exact or previous is None or previous[0] != kind:
            self._units[key] = (kind, peak)
            return
        self._units[key] = (kind, max(peak, previous[1]))

    def peak_of(self, key: str) -> int | None:
        """Return the peak the unit *key* was last measured at, or None when it never was."""
        entry = self._units.get(key)
        return None if entry is None else entry[1]

    def largest(self, kind: str) -> int:
        """Return the largest peak among the units of *kind*, 0 when none is measured."""
        return max((peak for unit_kind, peak in self._units.values() if unit_kind == kind),
                   default=0)

    def count(self, kind: str) -> int:
        """Return how many units of *kind* are measured."""
        return sum(1 for unit_kind, _ in self._units.values() if unit_kind == kind)

    def kinds(self) -> set[str]:
        """Return every kind with a measured unit."""
        return {kind for kind, _ in self._units.values()}

    def heaviest(self, limit: int) -> list[tuple[int, str]]:
        """Return up to *limit* units as (peak, key), heaviest first."""
        return sorted(((peak, key) for key, (_, peak) in self._units.items()),
                      reverse=True)[:limit]
