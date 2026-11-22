# job_resolution.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Resolves the job count of a build or a test run from the flag, the config and the default."""

from __future__ import annotations

from .build_admission import default_jobs


def resolve_jobs(explicit: int | None, configured: int | None) -> int:
    """Returns the job count: *explicit* when it is above 0, else *configured* when it is above 0,
    else :func:`sushicore.build_admission.default_jobs`.

    Args:
        explicit: The ``-j`` value; None when the flag was not given.
        configured: The ``build_jobs`` config key; None or 0 when it is absent.
    """
    if explicit is not None and explicit > 0:
        return explicit
    if configured is not None and configured > 0:
        return configured
    return default_jobs()
