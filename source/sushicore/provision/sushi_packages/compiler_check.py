# compiler_check.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Refuses a build tree configured with a compiler other than the one a package key names."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from ...cmake_cache import cached_value
from .package_error import PackageError
from .toolchain_identity import Probe, compiler_identity, run_probe


class CompilerCheck:
    """Compares the identity of a tree's cached compiler with an expected identity."""

    def __init__(self, probe: Probe = run_probe,
                 warn: Callable[[str], None] = lambda _text: None) -> None:
        """Bind the check to its probe and its warning sink.

        Args:
            probe: Runs ``<compiler> --version``; replaced in tests.
            warn: Receives the warning for a tree with no cache.
        """
        self._probe = probe
        self._warn = warn

    def verify(self, build_tree: Path, expected: str) -> None:
        """Probe the ``CMAKE_CXX_COMPILER`` cached in *build_tree* and compare it with *expected*.

        A tree with no cache is not yet configured, so there is nothing to compare, and one
        warning says so.

        Raises:
            PackageError: The cached compiler has another identity than *expected*.
        """
        cached = cached_value(build_tree, "CMAKE_CXX_COMPILER")
        if not cached:
            self._warn(f"{build_tree} has no CMakeCache.txt yet; its compiler is not checked.")
            return
        found = compiler_identity(cached, self._probe)
        if found != expected:
            raise PackageError(
                f"{build_tree} was configured with {cached} (identity {found}) and the key names "
                f"identity {expected}; a package is never shared across toolchains. Point the "
                "library's CLI at the consumer's compiler.")
