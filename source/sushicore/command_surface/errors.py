# errors.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The failures the canonical command surface reports, all derived from one base."""

from __future__ import annotations

from ..errors import SushiCoreError


class CommandSurfaceError(SushiCoreError, ValueError):
    """Reports a declaration of a canonical command that cannot be used."""


class UnknownSanitizerError(CommandSurfaceError):
    """Reports a ``--sanitize`` value that names a sanitizer the command does not build."""


class SanitizerConflictError(CommandSurfaceError):
    """Reports a ``--sanitize`` set whose sanitizers cannot share one build."""


class BuildTypeError(CommandSurfaceError):
    """Reports a set of build types that is empty or whose default is not among them."""


class DomainPanelError(CommandSurfaceError):
    """Reports a domain panel that is empty or takes the name of a canonical panel."""


class UnknownVerbError(CommandSurfaceError):
    """Reports a verb that is not in the canonical verb list."""


class ParameterNameError(CommandSurfaceError):
    """Reports a command parameter whose name another parameter of the command already takes."""
