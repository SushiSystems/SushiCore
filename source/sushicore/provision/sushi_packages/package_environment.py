# package_environment.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Assembles the environment a library build runs in."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping

#: Set in every nested build, so a library CLI knows a ``<NAME>_PACKAGE`` came from its parent.
K_MARKER = "SUSHISTACK_PACKAGE_NESTED"

#: Carries the consumer's compiler to the library CLI, which honours it over its config.
K_COMPILER = "SUSHISTACK_CXX"

#: The suffix of the variable that hands a package prefix to a nested build.
K_SUFFIX = "_PACKAGE"


def package_variable(name: str) -> str:
    """Return the variable that hands the prefix of *name* to a nested build."""
    return f"{name.upper()}{K_SUFFIX}"


class PackageEnvironment:
    """Builds the environment of a library build from the parent's and the chosen packages."""

    def __init__(self, base: Mapping[str, str]) -> None:
        """Bind the assembly to the parent environment.

        Args:
            base: The environment the CLI itself runs in.
        """
        self._base = base

    def assemble(self, compiler: str, below: Mapping[str, Path]) -> dict[str, str]:
        """Return the environment for a build with *compiler* against the packages *below*.

        It carries the compiler, one ``<NAME>_PACKAGE`` per package in *below* holding its
        prefix, and the nested marker. A ``<NAME>_PACKAGE`` the parent had for another library
        is dropped. No ``<NAME>_DIR`` variable is set.
        """
        env = {key: value for key, value in self._base.items()
               if not key.upper().endswith(K_SUFFIX)}
        env[K_COMPILER] = compiler
        env[K_MARKER] = "1"
        for name, prefix in below.items():
            env[package_variable(name)] = str(prefix)
        return env
