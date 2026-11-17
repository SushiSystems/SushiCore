# cmake_driver.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Invokes cmake and ctest for a module that supplies its own build policy.

The reasoning is in docs/architecture/OVERVIEW.md, section `cmake_driver`.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Mapping, Sequence

from .cmake_cache import cached_value, compiler_changed, generator_sentinel, is_stale
from .cmake_tool_config import CMakeToolConfig
from .errors import SushiCoreError
from .message_console import MessageConsole
from .proc import CommandRunner


#: The endings of the steps a dry run lists for a tree with CONFIGURE_DEPENDS globs, built or not.
_K_REGENERATION_STEPS = ("Re-checking globbed directories...", "Re-running CMake...")


def option_value(args: Sequence[str], option: str) -> str | None:
    """Return the value of *option* in a cmake argv, given as two words or as one."""
    for index, word in enumerate(args):
        if word == option and index + 1 < len(args):
            return args[index + 1]
        if word.startswith(option) and len(word) > len(option):
            return word[len(option):]
    return None


def _definition(args: Sequence[str], name: str) -> str | None:
    """Return the value a cmake argv gives the cache entry *name* through ``-D``, or None."""
    prefix = f"-D{name}="
    for word in args:
        if word.startswith(prefix):
            return word[len(prefix):]
    return None

_DEFAULT_DOXYGEN_HINT = (
    "  - Windows: winget install DimitriVanHeesch.Doxygen\n"
    "  - Linux:   apt-get install -y doxygen graphviz\n"
    "  - macOS:   brew install doxygen graphviz\n"
    "  - or set doxygen_exe in config.local.toml to an existing doxygen binary.")



def compiler_scratch(build_dir: Path) -> Path:
    """The folder a build of *build_dir* gives its compilers for temporaries."""
    return Path(build_dir) / "compiler_tmp"


def with_scratch(env: Mapping[str, str] | None, scratch: Path) -> dict[str, str]:
    """Copy *env*, or the live environment when None, with TMP and TEMP set to *scratch*."""
    merged = {k: v for k, v in (os.environ if env is None else env).items()
              if k.upper() not in ("TMP", "TEMP")}
    merged["TMP"] = merged["TEMP"] = str(scratch)
    return merged


class CleanTreeError(SushiCoreError):
    """Reports a build tree that could not be removed completely."""


class CMakeDriver:
    """The cmake and ctest half of what five project.py copies shared, over real build trees.

    It keeps the promise of :class:`sushicore.cmake_driver_port.CMakeDriverPort`.

    @param console A CLI's console module.
    @param runner  A :class:`sushicore.proc.CommandRunner`, such as :class:`sushicore.proc.Runner`.
    """

    __slots__ = ("_console", "_runner")

    def __init__(self, console: MessageConsole, runner: CommandRunner) -> None:
        self._console = console
        self._runner = runner

    def cmake(self, cfg: CMakeToolConfig) -> str:
        """The cmake executable: the configured path if set, else 'cmake'."""
        return cfg.expand(cfg.cmake_exe) if cfg.cmake_exe else "cmake"

    def ctest(self, cfg: CMakeToolConfig) -> str:
        """The ctest executable: the configured path if set, else 'ctest'."""
        return cfg.expand(cfg.ctest_exe) if cfg.ctest_exe else "ctest"

    def tree_exists(self, build_dir: Path) -> bool:
        """Whether a build tree is at *build_dir*."""
        return build_dir.is_dir()

    def tree_is_current(self, cfg: CMakeToolConfig, build_dir: Path,
                        env: Mapping[str, str] | None = None,
                        targets: Sequence[str] = ()) -> bool:
        """Whether the Ninja tree at *build_dir* has nothing left to build, by a dry run of its build.

        *targets* narrows the dry run to the targets a CLI builds; none asks of the whole tree.
        A tree of another generator, or a dry run that fails, reads as not current. The tree's own
        regeneration runs first for real, and its two steps are left out of the dry run.
        """
        if cached_value(build_dir, "CMAKE_GENERATOR") not in ("Ninja", "Ninja Multi-Config"):
            return False
        command = [self.cmake(cfg), "--build", str(build_dir)]
        regenerated, _, _ = self._runner.capture([*command, "--target", "build.ninja"], build_dir, env)
        if regenerated != 0:
            return False
        for target in targets:
            command += ["--target", target]
        code, stdout, _ = self._runner.capture([*command, "--", "-n"], build_dir, env)
        steps = [line for line in stdout.splitlines() if line.startswith("[")]
        return code == 0 and ("no work to do" in stdout
                              or bool(steps) and all(line.endswith(_K_REGENERATION_STEPS) for line in steps))

    def cached_value(self, build_dir: Path, entry: str) -> str | None:
        """The value the tree's cache holds for *entry*; see :func:`sushicore.cmake_cache.cached_value`."""
        return cached_value(build_dir, entry)

    def needs_configure(self, build_dir: Path, generator: str, *,
                        expect: Mapping[str, str] | None = None,
                        root: Path | None = None) -> bool:
        """Whether *build_dir* must be configured before it can be built.

        @param expect Cache entry to required value. A single-config generator
            bakes these into the tree, so a mismatch cannot be corrected by a
            flag on the build command and forces a reconfigure.
        @param root When given, also reject a tree configured against a
            different source path -- see :func:`sushicore.cmake_cache.is_stale`.
        """
        if not build_dir.is_dir():
            return True
        if not (build_dir / generator_sentinel(generator)).is_file():
            return True
        if root is not None and is_stale(build_dir, root):
            self._console.warn(
                "Build tree was configured for a different source path "
                "(e.g. a Docker volume build); reconfiguring from scratch.")
            return True
        for entry, wanted in (expect or {}).items():
            if cached_value(build_dir, entry) != wanted:
                return True
        return False

    def configure(self, args: Sequence[str], cwd: Path,
                  env: Mapping[str, str] | None = None) -> int:
        """Run a configure whose argv the caller assembled.

        A cache configured with a compiler at another path is deleted first; the reason is
        in docs/architecture/OVERVIEW.md, under `cmake_driver`.
        """
        self._drop_cache_of_another_compiler(list(args))
        return self._runner.run(list(args), cwd, env)

    def _drop_cache_of_another_compiler(self, args: list[str]) -> None:
        """Delete the cache of the tree *args* configures when its compiler path differs."""
        build_dir = option_value(args, "-B")
        compiler = _definition(args, "CMAKE_CXX_COMPILER")
        if not build_dir or not compiler or not compiler_changed(Path(build_dir), compiler):
            return
        self._console.warn(
            f"The build tree was configured with another compiler path; "
            f"configuring {build_dir} from an empty cache.")
        (Path(build_dir) / "CMakeCache.txt").unlink()

    def compile(self, cfg: CMakeToolConfig, build_dir: Path, cwd: Path,
                env: Mapping[str, str] | None, *,
                config: str | None = None, targets: Sequence[str] = (),
                jobs: int | None = None) -> int:
        """Bring an already-configured tree up to date.

        Args:
            config: The configuration to build; read from the tree's own cache when None.
            jobs: When set, passed as --parallel before the targets.

        The compilers write their temporaries to the tree's own scratch folder, emptied when the
        build ends.
        """
        if config is None:
            config = cached_value(build_dir, "CMAKE_BUILD_TYPE") or "Release"
        cmd = [self.cmake(cfg), "--build", str(build_dir), "--config", config]
        if jobs:
            cmd += ["--parallel", str(jobs)]
        for target in targets:
            cmd += ["--target", target]
        scratch = compiler_scratch(build_dir)
        scratch.mkdir(parents=True, exist_ok=True)
        try:
            return self._runner.run(cmd, cwd, with_scratch(env, scratch))
        finally:
            shutil.rmtree(scratch, ignore_errors=True)

    def ctest_run(self, cfg: CMakeToolConfig, build_dir: Path, env: Mapping[str, str] | None, *,
                  label_regex: str | None = None, exclude_label_regex: str | None = None,
                  filter: str | None = None,
                  repeat: int = 0, jobs: int | None = None,
                  config: str | None = None, output_junit: Path | None = None,
                  shuffle_seed: int | None = None, gtest_filter: str | None = None,
                  resource_spec_file: Path | None = None) -> int:
        """Run ctest over *build_dir*, draining its output.

        Args:
            exclude_label_regex: A ctest -LE pattern; matching labels are left out.
            filter: A ctest -R pattern over the ``Suite.Case`` names.
            repeat: Re-run each selected test until it fails or this many runs pass.
            output_junit: Where CTest writes a JUnit file; give an absolute path.
            gtest_filter: When set, GTEST_FILTER in every test's environment; a test's own wins.
        """
        cmd = [self.ctest(cfg), "--test-dir", str(build_dir), "--output-on-failure"]
        if label_regex:
            cmd += ["-L", label_regex]
        if exclude_label_regex:
            cmd += ["-LE", exclude_label_regex]
        if filter:
            cmd += ["-R", filter]
        if repeat > 0:
            cmd += ["--repeat", f"until-fail:{repeat}"]
            self._console.info(
                f"Repeating each test up to {repeat}x (stop on first failure).")
        if jobs:
            cmd += ["--parallel", str(jobs)]
        if config:
            cmd += ["-C", config]
        if output_junit:
            cmd += ["--output-junit", str(output_junit)]
        if resource_spec_file:
            cmd += ["--resource-spec-file", str(resource_spec_file)]
        handed_on: dict[str, str] = {}
        if shuffle_seed is not None:
            handed_on.update(GTEST_SHUFFLE="1", GTEST_RANDOM_SEED=str(shuffle_seed))
        if gtest_filter:
            handed_on["GTEST_FILTER"] = gtest_filter
        if handed_on:
            env = {**(os.environ if env is None else env), **handed_on}
        return self._runner.run_drained(cmd, build_dir, env)

    def clean_tree(self, build_dir: Path) -> None:
        """Remove *build_dir* and say what happened.

        Raises:
            CleanTreeError: The tree is still there after the removal, such as one holding a file
                another program has open.
        """
        if not build_dir.is_dir():
            self._console.info(f"{build_dir} does not exist, nothing to clean.")
            return
        self._console.info(f"Removing {build_dir}...")
        shutil.rmtree(build_dir, ignore_errors=True)
        if build_dir.exists():
            raise CleanTreeError(
                f"{build_dir} could not be removed completely; close any program that holds a file "
                "in it and clean again.")
        self._console.success(f"{build_dir} removed.")

    def doxygen(self, cfg: CMakeToolConfig, doxyfile: Path, cwd: Path,
                env: Mapping[str, str] | None, *,
                install_hint: str = _DEFAULT_DOXYGEN_HINT) -> int:
        """Run Doxygen over *doxyfile*, or explain why it cannot.

        Args:
            install_hint: Platform installation guidance appended to the not-installed message;
                the common per-platform commands when omitted.

        Raises:
            ValueError: *doxyfile* does not live under cwd.
        """
        if not doxyfile.is_file():
            self._console.error(f"Doxyfile not found at {doxyfile}.")
            return 1
        doxy = cfg.expand(cfg.doxygen_exe) if cfg.doxygen_exe else "doxygen"
        if self._runner.resolve_exe(doxy, env) == doxy and not Path(doxy).is_file():
            self._console.error(
                "Doxygen is not installed or not on PATH.\n" + install_hint)
            return 1
        # The child resolves this against cwd, in POSIX form; see docs/architecture/OVERVIEW.md.
        argument = doxyfile.relative_to(cwd).as_posix()
        return self._runner.run([doxy, argument], cwd, env)
