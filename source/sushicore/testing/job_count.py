# job_count.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Chooses how many tests run at once when the command is given no job count."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from ..memory_reading import K_RESERVE_MB
from .labels import TestLabel

#: The memory one running medium or large test is counted to hold, in megabytes.
K_TEST_SHARE_MB = 1024

#: The memory one running small test is counted to hold, in megabytes.
K_SMALL_SHARE_MB = 256


@dataclass(frozen=True, slots=True)
class JobChoice:
    """The job count of a run and the figures it came from.

    Attributes:
        jobs: How many tests run at once, at least one.
        cores: The cores the machine has.
        free_mb: The memory free when the choice was made, in megabytes.
        share_mb: The memory each running test was counted to hold, in megabytes.
    """

    jobs: int
    cores: int
    free_mb: int
    share_mb: int = K_TEST_SHARE_MB

    def line(self) -> str:
        """Return the line the run prints to name the count and what bounded it."""
        return (f"Jobs: {self.jobs} (cores {self.cores}, free memory {self.free_mb} MB "
                f"less {K_RESERVE_MB} MB reserved, {self.share_mb} MB per test)")


def share_of(sizes: Iterable[TestLabel]) -> int:
    """Return the memory share, in megabytes, of a run over *sizes*: the largest share of any of them.

    A run of small tests alone is counted at the small share; a run that holds a medium or a large
    test, or none at all, such as one of the quarantined tests, at the medium share.

    A medium or large test is counted at 1024 MB: a device runtime, its queue and the buffers of the
    case. A small test touches the memory of its own process only, with no device, no file and one
    thread: the program's image, GoogleTest, the logger and the heap of the cases of its shard, which
    run one after another. A quarter of the medium share leaves four times that room. It is a first
    figure that the owner's machine calibrates with a measured run, as it does the time limits.
    """
    chosen = tuple(sizes)
    return K_SMALL_SHARE_MB if chosen and all(size is TestLabel.SMALL for size in chosen) else K_TEST_SHARE_MB


def choose_jobs(cores: int | None, free_mb: int, share_mb: int = K_TEST_SHARE_MB) -> JobChoice:
    """Return one job per core, lowered until the jobs' shares fit the free memory.

    Args:
        cores: The core count, or ``None`` when the machine cannot tell, which counts as one.
        free_mb: The physical memory free now, in megabytes.
        share_mb: The memory one running test is counted to hold, from :func:`share_of`.
    """
    count = max(1, cores or 1)
    fitting = max(1, (free_mb - K_RESERVE_MB) // share_mb)
    return JobChoice(jobs=min(count, fitting), cores=count, free_mb=free_mb, share_mb=share_mb)
