# __init__.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Dependency provisioning shared by hub and every module CLI.

See ``docs/design/PROVISION.md``.
"""

from ._output import bind_console

__all__ = ["bind_console"]
