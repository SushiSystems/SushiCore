# output_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The in-memory console adapter provision tests pass to what prints."""

from __future__ import annotations

from typing import final

from ..console_memory import RecordingConsole


@final
class MemoryConsole(RecordingConsole):
    """The in-memory console adapter beside the real one: it records every call and prints nothing.

    Pass it to a step or a function as its ``console``; read what provision printed through
    ``calls``, ``texts`` and ``has_call``.
    """
