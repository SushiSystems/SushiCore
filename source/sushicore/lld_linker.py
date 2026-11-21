# lld_linker.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Decides when a Linux configure links with lld, and names the cache entries that say so.

The reasoning is in docs/architecture/OVERVIEW.md, section `lld_linker`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

#: The linker flag a clang driver reads.
K_LLD_FLAG = "-fuse-ld=lld"

#: The question a clang driver answers with the path of ``ld.lld``, or with the bare name when it has none.
K_LLD_PROBE = "-print-prog-name=ld.lld"

#: The C++ drivers whose personality is clang's, which take ``-fuse-ld=lld``.
K_CLANG_DRIVERS = ("clang++", "clang", "icpx", "icx")

#: The initial values of the three linker flag entries, which a project's own flags are added to.
K_LINKER_FLAG_ENTRIES = (
    "CMAKE_EXE_LINKER_FLAGS_INIT",
    "CMAKE_SHARED_LINKER_FLAGS_INIT",
    "CMAKE_MODULE_LINKER_FLAGS_INIT",
)

#: Words of a configure that already choose a linker, so the choice stays the caller's.
K_LINKER_CHOICES = ("-fuse-ld=", "CMAKE_LINKER_TYPE")


def lld_compiler(args: Sequence[str], compiler: str | None, platform: str) -> str | None:
    """Return the compiler to ask for lld, or None when the configure keeps the linker it has.

    @param args The cmake argv of the configure.
    @param compiler The C++ compiler the argv names, or None.
    @param platform ``sys.platform`` of the machine.
    """
    if not platform.startswith("linux") or not compiler:
        return None
    if Path(compiler).stem.lower() not in K_CLANG_DRIVERS:
        return None
    if any(choice in word for word in args for choice in K_LINKER_CHOICES):
        return None
    return compiler


def lld_is_found(probe_output: str) -> bool:
    """Return whether the compiler's answer to :data:`K_LLD_PROBE` names a file that exists."""
    answer = Path(probe_output.strip())
    return answer.is_absolute() and answer.is_file()


def lld_definitions() -> list[str]:
    """Return the ``-D`` words that make a tree link with lld."""
    return [f"-D{entry}={K_LLD_FLAG}" for entry in K_LINKER_FLAG_ENTRIES]
