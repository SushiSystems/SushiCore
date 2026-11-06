# cmake_driver_memory.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""A CMake driver that keeps its build trees in memory and records each call, with no process."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from .cmake_cache import same_path
from .cmake_driver import CMakeDriver, option_value


@dataclass(slots=True)
class MemoryTree:
    """One build tree held in memory.

    Attributes:
        generator: The generator the tree was configured with.
        cache: Cache entry to value, as CMakeCache.txt would hold them.
    """

    generator: str = "Ninja"
    cache: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CMakeCall:
    """One command the driver was asked to run.

    Attributes:
        method: The driver method called: configure, compile, ctest_run or doxygen.
        arguments: The arguments that method was given, by name.
    """

    method: str
    arguments: Mapping[str, Any]


class MemoryCMakeDriver:
    """Keeps the promise of :class:`sushicore.cmake_driver_port.CMakeDriverPort` in memory.

    A command answers the next exit code scripted with :meth:`script`, else 0. A configure whose argv
    names a tree with ``-B`` leaves that tree configured with the argv's ``-G`` and ``-D`` values.

    Args:
        console: Receives the warnings and the messages :class:`CMakeDriver` would print.
        doxyfiles: The Doxyfiles that exist.
    """

    def __init__(self, console, *, doxyfiles: Sequence[Path] = ()) -> None:
        """Start with no trees, no recorded calls and no scripted exit codes."""
        self._console = console
        self._doxyfiles = set(doxyfiles)
        self._trees: dict[Path, MemoryTree] = {}
        self._codes: list[int] = []
        self._calls: list[CMakeCall] = []

    @property
    def calls(self) -> list[CMakeCall]:
        """Return the commands recorded so far, in order."""
        return list(self._calls)

    def add_tree(self, build_dir: Path, *, generator: str = "Ninja",
                 cache: Mapping[str, str] | None = None) -> "MemoryCMakeDriver":
        """Put a configured tree at *build_dir* and return this driver."""
        self._trees[Path(build_dir)] = MemoryTree(generator, dict(cache or {}))
        return self

    def script(self, exit_code: int) -> "MemoryCMakeDriver":
        """Queue the exit code of the next command and return this driver."""
        self._codes.append(exit_code)
        return self

    def cmake(self, cfg) -> str:
        """Returns the cmake executable: the configured path if set, else 'cmake'."""
        return CMakeDriver.cmake(self, cfg)

    def ctest(self, cfg) -> str:
        """Returns the ctest executable: the configured path if set, else 'ctest'."""
        return CMakeDriver.ctest(self, cfg)

    def tree_exists(self, build_dir: Path) -> bool:
        """Returns whether a tree is held at *build_dir*."""
        return Path(build_dir) in self._trees

    def cached_value(self, build_dir: Path, entry: str) -> str | None:
        """Returns the value the tree's cache holds for *entry*, or None."""
        tree = self._trees.get(Path(build_dir))
        return tree.cache.get(entry) if tree else None

    def needs_configure(self, build_dir: Path, generator: str, *,
                        expect: Mapping[str, str] | None = None,
                        root: Path | None = None) -> bool:
        """Returns whether *build_dir* is absent, of another generator, stale or off *expect*."""
        tree = self._trees.get(Path(build_dir))
        if tree is None or tree.generator != generator:
            return True
        home = tree.cache.get("CMAKE_HOME_DIRECTORY")
        if root is not None and home and not same_path(home, str(root)):
            self._console.warn(
                "Build tree was configured for a different source path "
                "(e.g. a Docker volume build); reconfiguring from scratch.")
            return True
        return any(tree.cache.get(entry) != wanted for entry, wanted in (expect or {}).items())

    def configure(self, args: Sequence[str], cwd: Path, env=None) -> int:
        """Records the configure, configures the tree its argv names and returns the scripted code."""
        argv = list(args)
        build_dir = option_value(argv, "-B")
        if build_dir:
            tree = self._trees.setdefault(Path(build_dir), MemoryTree())
            tree.generator = option_value(argv, "-G") or tree.generator
            tree.cache.update(_definitions(argv))
        return self._answer("configure", args=tuple(argv), cwd=cwd, env=env)

    def compile(self, cfg, build_dir: Path, cwd: Path, env, *,
                config: str | None = None, targets: Sequence[str] = (),
                jobs: int | None = None) -> int:
        """Records the build, its configuration read from the tree when None, and returns the code."""
        if config is None:
            config = self.cached_value(build_dir, "CMAKE_BUILD_TYPE") or "Release"
        return self._answer("compile", build_dir=build_dir, cwd=cwd, env=env, config=config,
                            targets=tuple(targets), jobs=jobs)

    def ctest_run(self, cfg, build_dir: Path, env, *,
                  label_regex: str | None = None, exclude_label_regex: str | None = None,
                  filter: str | None = None,
                  repeat: int = 0, jobs: int | None = None,
                  config: str | None = None, output_junit: Path | None = None,
                  shuffle_seed: int | None = None) -> int:
        """Records the test run and returns the scripted code."""
        return self._answer("ctest_run", build_dir=build_dir, env=env, label_regex=label_regex,
                            exclude_label_regex=exclude_label_regex, filter=filter,
                            repeat=repeat, jobs=jobs, config=config,
                            output_junit=output_junit, shuffle_seed=shuffle_seed)

    def clean_tree(self, build_dir: Path) -> bool:
        """Drops the tree at *build_dir*, says so, and returns True."""
        if self._trees.pop(Path(build_dir), None) is None:
            self._console.info(f"{build_dir} does not exist, nothing to clean.")
            return True
        self._console.info(f"Removing {build_dir}...")
        self._console.success(f"{build_dir} removed.")
        return True

    def doxygen(self, cfg, doxyfile: Path, cwd: Path, env, *, install_hint: str = "") -> int:
        """Records the Doxygen run and returns the scripted code, or 1 when *doxyfile* is absent."""
        if Path(doxyfile) not in self._doxyfiles:
            self._console.error(f"Doxyfile not found at {doxyfile}.")
            return 1
        return self._answer("doxygen", doxyfile=doxyfile, cwd=cwd, env=env)

    def _answer(self, method: str, **arguments: Any) -> int:
        """Record one call and return the next scripted exit code, or 0."""
        self._calls.append(CMakeCall(method, arguments))
        return self._codes.pop(0) if self._codes else 0


def _definitions(args: Sequence[str]) -> dict[str, str]:
    """Return every cache entry a cmake argv sets with ``-DNAME=VALUE``, its ``:TYPE`` dropped."""
    entries: dict[str, str] = {}
    for word in args:
        if word.startswith("-D") and "=" in word:
            name, value = word[2:].split("=", 1)
            entries[name.split(":", 1)[0]] = value
    return entries
