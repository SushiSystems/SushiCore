# job_count.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Chooses how many tests run at once when the command is given no job count."""

from __future__ import annotations

from dataclasses import dataclass

from ..build_gate import K_RESERVE_MB

#: The memory one running test is counted to hold, in megabytes.
K_TEST_SHARE_MB = 1024


@dataclass(frozen=True, slots=True)
class JobChoice:
    """The job count of a run and the figures it came from.

    Attributes:
        jobs: How many tests run at once, at least one.
        cores: The cores the machine has.
        free_mb: The memory free when the choice was made, in megabytes.
    """

    jobs: int
    cores: int
    free_mb: int

    def line(self) -> str:
        """Return the line the run prints to name the count and what bounded it."""
        return (f"Jobs: {self.jobs} (cores {self.cores}, free memory {self.free_mb} MB "
                f"less {K_RESERVE_MB} MB reserved, {K_TEST_SHARE_MB} MB per test)")


def choose_jobs(cores: int | None, free_mb: int) -> JobChoice:
    """Return one job per core, lowered until the jobs' shares fit the free memory.

    Args:
        cores: The core count, or ``None`` when the machine cannot tell, which counts as one.
        free_mb: The physical memory free now, in megabytes.
    """
    count = max(1, cores or 1)
    fitting = max(1, (free_mb - K_RESERVE_MB) // K_TEST_SHARE_MB)
    return JobChoice(jobs=min(count, fitting), cores=count, free_mb=free_mb)
