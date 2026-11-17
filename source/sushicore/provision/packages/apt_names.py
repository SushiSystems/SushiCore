# apt_names.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Maps apt package names to the native names of the other Linux package managers."""

from __future__ import annotations

K_APT_TO_DNF: dict[str, list[str]] = {
    "build-essential":     ["gcc", "gcc-c++", "make"],
    "ninja-build":         ["ninja-build"],
    "libhwloc-dev":        ["hwloc-devel"],
    "libgtest-dev":        ["gtest-devel"],
    "ocl-icd-opencl-dev":  ["ocl-icd"],
    "ocl-icd-libopencl1":  [],
    "pkg-config":          ["pkgconf"],
}

K_APT_TO_PACMAN: dict[str, list[str]] = {
    "build-essential":     ["base-devel"],
    "ninja-build":         ["ninja"],
    "libhwloc-dev":        ["hwloc"],
    "libgtest-dev":        ["gtest"],
    "ocl-icd-opencl-dev":  ["ocl-icd"],
    "ocl-icd-libopencl1":  [],
    "pkg-config":          ["pkgconf"],
}

K_APT_TO_ZYPPER: dict[str, list[str]] = {
    "build-essential":     ["gcc", "gcc-c++", "make"],
    "ninja-build":         ["ninja"],
    "libhwloc-dev":        ["hwloc-devel"],
    "libgtest-dev":        ["gtest"],
    "ocl-icd-opencl-dev":  ["ocl-icd"],
    "ocl-icd-libopencl1":  [],
    "pkg-config":          ["pkgconf"],
}


def translate_names(apt_pkgs: list[str], table: dict[str, list[str]]) -> list[str]:
    """Map each apt-format package name in *apt_pkgs* through *table*."""
    out: list[str] = []
    for pkg in apt_pkgs:
        out.extend(table.get(pkg, [pkg]))
    return out
