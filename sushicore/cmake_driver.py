"""Invoking cmake and ctest on behalf of a module that has a build policy.

This knows the shape of a cmake command line. It does not know a single cache
variable's name: which -D flags a module passes, which targets it has and which
suites it runs are policy, and policy stays in the module. Everything
module-specific arrives as a parameter -- `expect` for the cache entries a tree
must already agree with, `targets` for what to build, `label_regex` for which
tests to select.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Mapping, Sequence

from .cmake_cache import cached_value, generator_sentinel, is_stale


class CMakeDriver:
    """The cmake and ctest half of what five project.py copies shared.

    @param console A CLI's console module.
    @param runner  A :class:`sushicore.proc.Runner`.
    """

    __slots__ = ("_console", "_runner")

    def __init__(self, console, runner) -> None:
        self._console = console
        self._runner = runner

    # -- executables ----------------------------------------------------

    def cmake(self, cfg) -> str:
        """The cmake executable: the configured path if set, else 'cmake'."""
        return cfg.expand(cfg.cmake_exe) if cfg.cmake_exe else "cmake"

    def ctest(self, cfg) -> str:
        """The ctest executable: the configured path if set, else 'ctest'."""
        return cfg.expand(cfg.ctest_exe) if cfg.ctest_exe else "ctest"

    # -- configure ------------------------------------------------------

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

    def configure(self, args: Sequence[str], cwd: Path, env=None) -> int:
        """Run a configure whose argv the caller assembled."""
        return self._runner.run(list(args), cwd, env)

    # -- build ----------------------------------------------------------

    def compile(self, cfg, build_dir: Path, cwd: Path, env, *,
                config: str | None = None, targets: Sequence[str] = ()) -> int:
        """Bring an already-configured tree up to date.

        @param config The configuration to build. When None it is read from the
            tree's own cache, because a caller that did not configure this tree
            has no business choosing one.
        """
        if config is None:
            config = cached_value(build_dir, "CMAKE_BUILD_TYPE") or "Release"
        cmd = [self.cmake(cfg), "--build", str(build_dir), "--config", config]
        for target in targets:
            cmd += ["--target", target]
        return self._runner.run(cmd, cwd, env)

    # -- test -----------------------------------------------------------

    def ctest_run(self, cfg, build_dir: Path, env, *,
                  label_regex: str | None = None, filter: str | None = None,
                  repeat: int = 0) -> int:
        """Run ctest over *build_dir*, draining its output.

        @param filter A ctest -R pattern. gtest_discover_tests registers cases
            as "Suite.Case", so this filters those names directly -- a richer
            alternative to --gtest_filter.
        @param repeat Re-run each selected test until it fails or this many runs
            pass, the native ctest way to flush out flakiness.
        """
        cmd = [self.ctest(cfg), "--test-dir", str(build_dir), "--output-on-failure"]
        if label_regex:
            cmd += ["-L", label_regex]
        if filter:
            cmd += ["-R", filter]
        if repeat > 0:
            cmd += ["--repeat", f"until-fail:{repeat}"]
            self._console.info(
                f"Repeating each test up to {repeat}x (stop on first failure).")
        return self._runner.run_drained(cmd, build_dir, env)

    # -- clean ----------------------------------------------------------

    def clean_tree(self, build_dir: Path) -> None:
        """Remove *build_dir* and say what happened either way."""
        if build_dir.is_dir():
            self._console.info(f"Removing {build_dir}...")
            shutil.rmtree(build_dir, ignore_errors=True)
            self._console.success(f"{build_dir} removed.")
        else:
            self._console.info(f"{build_dir} does not exist, nothing to clean.")

    # -- docs -----------------------------------------------------------

    def doxygen(self, cfg, doxyfile: Path, cwd: Path, env, *,
                install_hint: str) -> int:
        """Run Doxygen over *doxyfile*, or explain why it cannot.

        @param install_hint Platform installation guidance, appended to the
            not-installed message. The module supplies it because the message
            names the module's own config file.
        @precondition doxyfile must live under cwd. Every module passes
            `root / ...` with `cwd=root`; a Doxyfile outside cwd raises
            ValueError out of relative_to rather than silently falling back to
            an absolute argument, which would change the command line for
            whichever module hit it first.
        """
        if not doxyfile.is_file():
            self._console.error(f"Doxyfile not found at {doxyfile}.")
            return 1
        doxy = cfg.expand(cfg.doxygen_exe) if cfg.doxygen_exe else "doxygen"
        if self._runner.resolve_exe(doxy, env) == doxy and not Path(doxy).is_file():
            self._console.error(
                "Doxygen is not installed or not on PATH.\n" + install_hint)
            return 1
        # The child resolves its argument against cwd, and every module passes a
        # path relative to the project root rather than an absolute one. Derive
        # it rather than asking for it twice: as_posix() is load-bearing on
        # Windows, where relative_to yields backslashes and str() would change
        # the command line.
        argument = doxyfile.relative_to(cwd).as_posix()
        return self._runner.run([doxy, argument], cwd, env)
