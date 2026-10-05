# errors.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026 Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The failures sushicore reports to a CLI's entry point as one line.

:func:`sushicore.entry.run` catches :class:`SushiCoreError` and nothing wider, so an error
that derives from it reaches the user as a message and anything else stays a traceback.
"""

from __future__ import annotations


class SushiCoreError(Exception):
    """Reports a failure the user can act on, as opposed to a defect in the CLI."""


class ConfigError(SushiCoreError, ValueError):
    """Reports a configuration file or value that cannot be used."""
