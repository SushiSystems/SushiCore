# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Dependency provisioning shared by hub and every module CLI.

See ``docs/agent/specs/2026-09-23-provision-design.md``.
"""

from ._output import bind_console

__all__ = ["bind_console"]
