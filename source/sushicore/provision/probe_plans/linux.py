# linux.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The probe plan of the Linux target."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import final

from ..config import ProvisionConfig
from ..dependency_home import DEFAULT_HOME, DependencyHome
from ..probe import binary_works, discover_installed_toolchains
from ..probe_plan import PROBE_PLANS, IProbePlan
from ..target import K_LINUX


@final
class LinuxProbePlan(IProbePlan):
    """Finds oneAPI ``icpx`` or the intel/llvm ``clang++`` on PATH and the Linux tool paths."""

    def __init__(self, *, home: DependencyHome = DEFAULT_HOME) -> None:
        """Bind the home whose roots the plan searches for installed toolchains.

        Args:
            home: The home whose dependency root the plan reads; the deprecated default home when omitted.
        """
        self._home = home

    def find_sycl_compiler(self, cfg: ProvisionConfig) -> tuple[str | None, str]:
        """Return the first working of oneAPI ``icpx`` and the intel/llvm ``clang++`` on PATH."""
        for cc in ("icpx", "clang++"):
            path = shutil.which(cc)
            if path and binary_works(path):
                return (cc, path)
        return (None, "")

    def resolve_local_config(self, cfg: ProvisionConfig) -> dict[str, str]:
        """Probe Linux-specific tool paths for the local config."""
        values: dict[str, str] = {}
        compiler, _path = self.find_sycl_compiler(cfg)
        if compiler == "clang++":
            values["cxx"] = "clang++"
            values["cc"] = "clang"
        oneapi = cfg.expand(cfg.oneapi_root) if cfg.oneapi_root else ""
        if oneapi and Path(oneapi, "setvars.sh").is_file():
            values["oneapi_root"] = oneapi
        discover_installed_toolchains(cfg, values, home=self._home)
        return values


PROBE_PLANS.register(K_LINUX, LinuxProbePlan())
