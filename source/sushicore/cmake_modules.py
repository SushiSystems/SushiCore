# cmake_modules.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Names the folder of CMake modules SushiCore ships, and puts it on a configure's module path.

What the modules hold is in source/sushicore/cmake/README.md.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

#: The folder of the CMake modules, ``SushiBuild.cmake`` among them, inside the installed package.
K_CMAKE_MODULES = Path(__file__).resolve().parent / "cmake"

#: The cache entry a configure finds ``include()`` modules through.
K_MODULE_PATH_ENTRY = "CMAKE_MODULE_PATH"


def with_cmake_modules(args: Sequence[str], modules: Path = K_CMAKE_MODULES) -> list[str]:
    """Return a cmake argv whose ``CMAKE_MODULE_PATH`` holds *modules*.

    A ``-DCMAKE_MODULE_PATH`` the argv already gives, typed or not, keeps its folders first and
    gains *modules* after them; an argv without one gains the definition at its end. The folder is
    written in forward slashes, which CMake reads on every platform.

    @param args The cmake argv of a configure.
    @param modules The folder to add; the package's own by default.
    """
    folder = modules.as_posix()
    argv = list(args)
    for index, word in enumerate(argv):
        name, separator, value = word.partition("=")
        if not separator or name.split(":")[0] != f"-D{K_MODULE_PATH_ENTRY}":
            continue
        folders = [entry for entry in value.split(";") if entry]
        if folder not in folders:
            argv[index] = f"{name}={';'.join([*folders, folder])}"
        return argv
    return [*argv, f"-D{K_MODULE_PATH_ENTRY}={folder}"]
