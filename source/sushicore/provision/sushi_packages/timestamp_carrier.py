# timestamp_carrier.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Gives a new package's unchanged files the modification time they had in the previous one."""

from __future__ import annotations

import filecmp
import logging
import os
from pathlib import Path
from typing import final

K_LOGGER = logging.getLogger(__name__)


@final
class TimestampCarrier:
    """Copies the timestamps of byte-identical files from an earlier install prefix to a new one.

    A build tool that reads headers through a stable link compares their modification times, so
    a fresh install of unchanged bytes would rebuild everything that includes them.
    """

    def carry(self, previous: Path, staged: Path) -> int:
        """Give each file of *staged* that equals the same relative file of *previous* its times.

        A file is compared by size first and by content only when the sizes agree. A file that
        differs, or that *previous* lacks, keeps its own time. A file that cannot be read or
        stamped is left as it is and logged.

        Returns:
            How many files took the time of their counterpart.
        """
        carried = 0
        for folder, _folders, names in os.walk(staged):
            for name in names:
                path = Path(folder) / name
                if self._carry_file(path, previous / path.relative_to(staged)):
                    carried += 1
        return carried

    @staticmethod
    def _carry_file(path: Path, earlier: Path) -> bool:
        """Stamp *path* with the times of *earlier* when both are regular files with equal bytes."""
        try:
            if path.is_symlink() or earlier.is_symlink() or not earlier.is_file():
                return False
            old = earlier.stat()
            if old.st_size != path.stat().st_size or not filecmp.cmp(path, earlier, shallow=False):
                return False
            os.utime(path, ns=(old.st_atime_ns, old.st_mtime_ns))
        except OSError as exc:
            K_LOGGER.warning("the time of %s could not be carried from %s: %s", path, earlier, exc)
            return False
        return True
