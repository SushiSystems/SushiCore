# package_request.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""What a consumer asks the package resolver for."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

from ..closure import DEFAULT_FRAGMENT


@dataclass(frozen=True, slots=True)
class PackageRequest:
    """The consumer, its compiler and its build type, and the choices it makes per library.

    Args:
        owner: The consumer's lower-case name.
        root: The consumer's checkout.
        compiler: The SYCL compiler the consumer builds with.
        build_type: The consumer's build type; lower-cased into the key.
        options: The extra ``build`` arguments of a library, by library name.
        configured: The ``<NAME>_DIR`` of a library from the config, by library name.
        fragment: The consumer's fragment, below *root*.
        vcpkg_root: The vcpkg tree the consumer uses, or None.
        triplet: The vcpkg triplet the consumer uses.
    """

    owner: str
    root: Path
    compiler: str
    build_type: str
    options: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    configured: Mapping[str, str] = field(default_factory=dict)
    fragment: str = DEFAULT_FRAGMENT
    vcpkg_root: Path | None = None
    triplet: str = ""
