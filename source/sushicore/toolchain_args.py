# toolchain_args.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Derives the C compiler and the vcpkg prefix a cmake configure is given.

The reasoning is in docs/architecture/OVERVIEW.md, section `toolchain_args`.
"""

from __future__ import annotations

import shutil
from pathlib import Path


#: The C driver that sits beside each C++ driver whose personality is fixed to C++.
K_C_SIBLINGS = {"clang++": "clang", "icpx": "icx"}


def c_compiler_for(cxx: str) -> str:
    """The C compiler slot for a C++-personality driver: its sibling C driver.

    clang++ and oneAPI's icpx hardcode C++ mode regardless of file extension, so
    pointing CMAKE_C_COMPILER at the same path breaks the C-language probe for a
    project declaring LANGUAGES CXX C. Each ships its C driver beside it; a bare
    name is looked up on the PATH.

    @param cxx The resolved C++ compiler path, or a bare name.
    @return The sibling C driver, or *cxx* unchanged when there is none.
    """
    path = Path(cxx)
    sibling_stem = K_C_SIBLINGS.get(path.stem.lower())
    if sibling_stem is None:
        return cxx
    if path.parent == Path("."):
        found = shutil.which(sibling_stem)
        return found if found else cxx
    sibling = path.with_name(sibling_stem + path.suffix)
    return str(sibling) if sibling.is_file() else cxx


def vcpkg_prefix(cfg, root: Path) -> str:
    """The vcpkg installed-tree prefix for this triplet, or '' when unavailable.

    Only meaningful on Windows, where the bundled vcpkg tree is what
    find_package uses to locate GoogleTest and hwloc.
    """
    vcpkg = cfg.resolved_vcpkg(root)
    return f"{vcpkg}/installed/{cfg.vcpkg_triplet}" if vcpkg else ""
