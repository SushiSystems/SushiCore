# profile.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Declares the facts one Sushi CLI states about itself.

The reasoning is in docs/architecture/OVERVIEW.md, section `profile`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

#: Names the file a release build writes at an install's root; docs/architecture/OVERVIEW.md.
RELEASE_MANIFEST = "sushi-release.json"

# One suffix per ToolConfig field, the same on every CLI; see docs/architecture/OVERVIEW.md.
_TOOL_ENV_SUFFIXES: Mapping[str, str] = {
    "cxx": "CXX",
    "generator": "CMAKE_GENERATOR",
    "vcpkg_root": "VCPKG_ROOT",
    "vs_vcvars": "VCVARS",
    "ninja_exe": "NINJA",
    "cmake_exe": "CMAKE",
    "ctest_exe": "CTEST",
    "rc_exe": "RC",
    "pkgconf_exe": "PKGCONF",
    "doxygen_exe": "DOXYGEN",
    "vcpkg_triplet": "VCPKG_TRIPLET",
    "target_bin": "TARGET_BIN",
}


# Environment variables that steer any build in the stack, whatever the module.
_COMMON_ENV_TOKENS: tuple[str, ...] = (
    "PATH", "CC", "CXX", "CMAKE", "NINJA", "VCPKG", "PKG_CONFIG",
    "LD_LIBRARY_PATH",
)


@dataclass(frozen=True)
class ModuleProfile:
    """The identity of one Sushi* module, as its CLI and the shared code see it.

    @param name          Display name used in messages, e.g. ``"SushiEngine"``.
    @param program       The command a user types, e.g. ``"se"``.
    @param env_prefix    Prefix on this CLI's environment overrides, e.g. ``"SE"``.
    @param root_marker   File whose presence marks the root of a checkout.
    @param release_manifest File whose presence marks the root of an unpacked
                         binary install, and tells the two forms apart.
    @param siblings      Sibling module directories this project builds in-tree.
    @param default_target Executable ``run`` falls back to with no target named.
    @param env_fields    Which config fields accept a prefixed override. Empty
                         means all of them, which is what every CLI but sushidsp
                         wants; sushidsp exposes a deliberate subset.
    @param env_of_interest Extra environment-variable tokens `<prog> env` shows
                         on top of the ones every build cares about.
    """

    name: str
    program: str
    env_prefix: str
    root_marker: str = "CMakeLists.txt"
    release_manifest: str = RELEASE_MANIFEST
    siblings: tuple[str, ...] = ()
    default_target: str = ""
    extra_env_overrides: Mapping[str, str] = field(default_factory=dict)
    env_fields: tuple[str, ...] = ()
    env_of_interest: tuple[str, ...] = ()

    def env_overrides(self) -> dict[str, str]:
        """Map each config field to the environment variable that overrides it.

        Derived from :data:`_TOOL_ENV_SUFFIXES` and this module's prefix, so the
        eleven-line table that used to sit verbatim in every CLI cannot drift.
        *extra_env_overrides* carries the ones that are genuinely this module's
        (``SUSHIRUNTIME_DIR`` and friends, which are shared across CLIs and so
        take no prefix).
        """
        wanted = set(self.env_fields) if self.env_fields else None
        derived = {
            field_name: f"{self.env_prefix}_{suffix}"
            for field_name, suffix in _TOOL_ENV_SUFFIXES.items()
            if wanted is None or field_name in wanted
        }
        derived.update(self.extra_env_overrides)
        return derived

    def env_tokens(self) -> tuple[str, ...]:
        """Environment variables `<prog> env` surfaces without ``--all``.

        The common set is what every build in the stack steers on; a module adds
        only what is genuinely its own (sushiruntime's oneAPI and CUDA
        variables, say). Shared so the four CLIs cannot quietly disagree about
        which variables count as build-relevant.
        """
        return _COMMON_ENV_TOKENS + tuple(self.env_of_interest)

    @property
    def key(self) -> str:
        """Return the lower-cased name this module is recorded under."""
        return self.name.lower()

    def markers(self) -> tuple[str, ...]:
        """Return every file whose presence marks this module's root.

        A checkout carries the root marker, an unpacked release carries the
        manifest, and a CLI invoked inside either has to find its root.
        """
        return (self.root_marker, self.release_manifest)

    def presence(self, root: Path) -> str:
        """Report how the module at *root* arrived: "binary" or "source".

        @param root Directory that carries one of :meth:`markers`.
        """
        return "binary" if (root / self.release_manifest).is_file() else "source"

    def not_a_project_message(self) -> str:
        """The error shown when a command runs outside a checkout."""
        return (
            f"Not inside a {self.name} project: no {' or '.join(self.markers())} "
            "found in the current directory or any parent. cd into the repo and "
            "try again."
        )

    def sibling_skip_dirs(self) -> tuple[str, ...]:
        """Directory names the executable search must prune.

        A module that builds a dependency in-tree must not offer that
        dependency's executables as its own, so the sibling list is exactly the
        skip list -- stated once here rather than repeated in discovery.py.
        """
        return self.siblings
