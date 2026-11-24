# errors.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The errors of the release train."""

from __future__ import annotations

from ..errors import SushiCoreError


class ReleaseTrainError(SushiCoreError):
    """A step of the train failed; the message names the library and the step."""
