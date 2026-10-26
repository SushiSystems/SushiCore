# __init__.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Sushi libraries consumed as built packages: key, store, builder and resolver.

See ``docs/agent/2026_10_26_PREBUILT_SUSHI_PACKAGES/SPEC.md``.
"""

from .consumer_build import RunDirs, configure_arguments, search_path_variable
from .default_resolver import default_resolver, effective_keep
from .package_error import PackageConflictError, PackageError
from .package_request import PackageRequest
from .package_resolver import PackageResolver
from .package_set import PackageSet, ResolvedPackage

__all__ = [
    "RunDirs",
    "PackageConflictError",
    "PackageError",
    "PackageRequest",
    "PackageResolver",
    "PackageSet",
    "ResolvedPackage",
    "configure_arguments",
    "default_resolver",
    "effective_keep",
    "search_path_variable",
]
