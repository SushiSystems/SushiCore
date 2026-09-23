# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""The configuration shape provision code reads, and a concrete one for standalone modules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..config_base import ToolConfig


class ProvisionConfig(Protocol):
    """The fields and helpers provision code reads from a CLI's config."""

    platform: str
    cmake_exe: str
    ctest_exe: str
    ninja_exe: str
    vs_vcvars: str
    vcpkg_root: str
    vcpkg_triplet: str
    pkgconf_exe: str
    doxygen_exe: str
    oneapi_root: str
    icx_compiler: str
    llvm_root: str
    acpp_exe: str

    @property
    def is_windows(self) -> bool:
        """Report whether the config was resolved for Windows."""

    def expand(self, value: str) -> str:
        """Expand ``~`` and environment variables in a path value."""


@dataclass
class ProvisionSettings(ToolConfig):
    """A :class:`ToolConfig` carrying the toolchain roots provision probes and writes."""

    oneapi_root: str = ""
    icx_compiler: str = ""
    llvm_root: str = ""
    acpp_exe: str = ""
