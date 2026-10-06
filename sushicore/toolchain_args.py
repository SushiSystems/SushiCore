# toolchain_args.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Derives the C compiler and the vcpkg prefix a cmake configure is given.

The reasoning is in docs/architecture/OVERVIEW.md, section `toolchain_args`.
"""

from __future__ import annotations

from pathlib import Path


def c_compiler_for(cxx: str) -> str:
    """The C compiler slot for a clang++-personality binary: its sibling clang.

    A clang++-personality binary hardcodes C++ mode regardless of file
    extension, so pointing CMAKE_C_COMPILER at the same path breaks the
    C-language probe for a project declaring LANGUAGES CXX C. The bundled
    intel-llvm toolchain ships a sibling clang next to it for that slot.

    @param cxx The resolved C++ compiler path.
    @return The sibling clang binary, or *cxx* unchanged when there is none.
    """
    path = Path(cxx)
    stem = path.stem
    if stem.lower() == "clang++":
        sibling = path.with_name(stem[:-2] + path.suffix)
        if sibling.is_file():
            return str(sibling)
    return cxx


def vcpkg_prefix(cfg, root: Path) -> str:
    """The vcpkg installed-tree prefix for this triplet, or '' when unavailable.

    Only meaningful on Windows, where the bundled vcpkg tree is what
    find_package uses to locate GoogleTest and hwloc.
    """
    vcpkg = cfg.resolved_vcpkg(root)
    return f"{vcpkg}/installed/{cfg.vcpkg_triplet}" if vcpkg else ""
