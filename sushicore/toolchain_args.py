"""Two derivations every cmake configure in this stack needs.

Only two. Assembling the full -D list is not here on purpose: SushiRuntime
splits its assembly across Windows and Linux, and SushiEngine deliberately omits
CMAKE_C_COMPILER because its runtime lane has no C sources. Both divergences are
real and documented where they live. Forcing them into one function would hide a
genuine difference behind a flag.
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
