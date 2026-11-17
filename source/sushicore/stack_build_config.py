# stack_build_config.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The configuration fields a module's build environment reads."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


class StackBuildConfig(Protocol):
    """What :class:`sushicore.build_env.StackBuildEnv` reads from a module's config.

    A module may add one ``<sibling>_dir`` field for each sibling its profile names; the cache key
    reads those by name, since the names come from the profile.
    """

    @property
    def platform(self) -> str:
        """The platform key the config was loaded for."""
        ...

    @property
    def vs_vcvars(self) -> str:
        """The configured Visual Studio environment script; empty when none is set."""
        ...

    @property
    def is_windows(self) -> bool:
        """Whether the config is for a Windows host."""
        ...

    @property
    def vcpkg_triplet(self) -> str:
        """The vcpkg triplet of the build."""
        ...

    def expand(self, value: str) -> str:
        """Expand ``~`` and environment variables in a path value."""
        ...

    def bundled_llvm_root(self, root: Path) -> Path | None:
        """Return the bundled LLVM tree of the checkout at *root*, or None."""
        ...

    def resolved_vcpkg(self, root: Path) -> str:
        """Return the vcpkg root of the checkout at *root*, empty when none."""
        ...
