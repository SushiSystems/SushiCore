# __init__.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The documentation bundle: what a repository publishes to docs.sushisystems.io."""

from __future__ import annotations

from .api_reference import ApiSource
from .bundle_manifest import K_SCHEMA_VERSION
from .commands import register_docs_commands
from .errors import (
    ApiReferenceError,
    DocsBundleError,
    PageError,
    PublishListError,
    ReleaseError,
)
from .producer import K_DEFAULT_OUTPUT, BundleProducer, BundleRequest, BundleResult

__all__ = [
    "ApiReferenceError",
    "ApiSource",
    "BundleProducer",
    "BundleRequest",
    "BundleResult",
    "DocsBundleError",
    "K_DEFAULT_OUTPUT",
    "K_SCHEMA_VERSION",
    "PageError",
    "PublishListError",
    "ReleaseError",
    "register_docs_commands",
]
