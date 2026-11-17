# adaptivecpp.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Builds AdaptiveCpp (acpp) from source, the secondary open-source SYCL toolchain."""

from __future__ import annotations

import glob as _glob
import os
import shutil
import tempfile
import typing
from pathlib import Path
from typing import Any, Callable, MutableMapping, Sequence

from sushicore.errors import CommitMismatchError
from sushicore.fragment_types import GitPin
from sushicore.proc import CommandRunner

from ..default_console import console_or_default
from .. import home as home_paths
from ..dependency_home import DEFAULT_HOME, DependencyHome
from ..download_checking import DownloadChecking
from ..git_client import GitClient
from ..glob_search import K_RC_GLOBS
from ..dependency_presence import named_manager
from ..install_location import ToolkitInstall
from ..licence_consent import Licence
from ..pinned_checkout import checkout_pinned
from ..process_run import provision_runner, run
from ..source_pins import base_git_pin
from ..llvm_plan import LLVM_PLANS, LlvmRequest
from ..install_context import InstallContext
from ..target import target_of
from ._process import _run_quiet
from .adaptivecpp_compat import confirm_timeout as _confirm_timeout  # noqa: F401  (deprecated)
from .adaptivecpp_compat import find_windows_llvm as _find_windows_llvm  # noqa: F401  (deprecated)
from .stamp import toolchains_dir
from .toolchain import ToolchainEnv

if typing.TYPE_CHECKING:
    from ..config import ProvisionConfig
    from ..packages import IPackageManager, LinuxPackageManager

__all__ = ["ADAPTIVECPP", "AdaptiveCppToolchain", "install_adaptivecpp"]

#: AdaptiveCpp release built from source; the base fragment pins its commit under ``adaptivecpp``.
ACPP_VERSION = "v24.10.0"
#: The repository AdaptiveCpp is fetched from.
ACPP_URL = "https://github.com/AdaptiveCpp/AdaptiveCpp.git"
#: The entry of the base fragment that pins the commit AdaptiveCpp is built from.
K_ACPP_PIN = "adaptivecpp"
#: clang/llvm major version used to build acpp.
ACPP_LLVM = "17"
#: Full LLVM release vendored on Windows when no LLVM dev install exists.
LLVM_WINDOWS_VERSION = "17.0.6"


@typing.final
class AdaptiveCppToolchain:
    """AdaptiveCpp built from source, the secondary SYCL toolchain."""

    key = "adaptivecpp"
    selection_field = "install_acpp"

    def __init__(self, *, home: DependencyHome = DEFAULT_HOME) -> None:
        """Bind the home :meth:`locate` reads; :meth:`install` reads the home of its context.

        Args:
            home: The home whose toolchains folder is searched; the deprecated default home when omitted.
        """
        self._home = home

    def locate(self, cfg: "ProvisionConfig") -> ToolkitInstall | None:
        """Return the prefix under the toolchains folder, or None when no ``acpp`` launcher is there."""
        prefix = toolchains_dir(home=self._home) / "adaptivecpp"
        launchers = (target_of(cfg).acpp_launcher, "acpp")
        if not any((prefix / "bin" / name).is_file() for name in launchers):
            return None
        return ToolkitInstall(root=prefix, version=None)

    def licences(self, ctx: InstallContext) -> list[Licence]:
        """Return no licence; the LLVM prompt is a size consent, not a licence."""
        return []

    def install(self, ctx: InstallContext, env: ToolchainEnv) -> bool:
        """Build AdaptiveCpp, record ``acpp_exe`` in *ctx* and warn when it is the only toolchain.

        Returns:
            True; a failed build only leaves the toolchain unavailable.
        """
        acpp = install_adaptivecpp(
            ctx.cfg, env.mgr, env.vcpkg, ctx.dry_run,
            assume_yes=ctx.assume_acpp_llvm,
            winget=named_manager(env.managers, "winget"), console=env.console, home=ctx.home,
            verifier=ctx.verifier)
        if acpp:
            ctx.resolved_paths["acpp_exe"] = acpp
        elif not ctx.selection.install_intel_llvm:
            message = ("AdaptiveCpp is the only toolchain selected but it did "
                       "not install; the project will not build.")
            env.console.warn(f"{message} {ctx.fallback_hint}".strip())
        return True


ADAPTIVECPP = AdaptiveCppToolchain()


def _find_windows_sdk_rc_dir(glob: Callable[[str], list[str]] | None = None) -> str:
    """Return the directory containing rc.exe from the Windows 10/11 SDK, or ''.

    Args:
        glob: Expands a glob pattern into the matching paths; ``glob.glob`` when omitted.
    """
    for pat in K_RC_GLOBS:
        hits = sorted((glob or _glob.glob)(pat))
        if hits:
            return str(Path(hits[-1]).parent)
    return ""


def install_adaptivecpp(cfg: "ProvisionConfig", mgr: "LinuxPackageManager | None",
                        vcpkg: "IPackageManager | None", dry_run: bool,
                        assume_yes: bool = False, *,
                        console: Any = None,
                        winget: "IPackageManager | None" = None,
                        which: Callable[[str], str | None] | None = None,
                        glob: Callable[[str], list[str]] | None = None,
                        llvm_bases: Sequence[Path] | None = None,
                        environ: MutableMapping[str, str] | None = None,
                        run_command: Callable[..., int] | None = None,
                        configure: Callable[[list[str], bool], bool] | None = None,
                        home: DependencyHome | None = None,
                        verifier: "DownloadChecking | None" = None,
                        runner: CommandRunner | None = None,
                        pin: GitPin | None = None,
                        ) -> str | None:
    """Build AdaptiveCpp from source; return the ``acpp`` executable path, or None on failure.

    Args:
        cfg: Resolved configuration; selects platform-specific paths and tools.
        dry_run: Report the action without touching the filesystem.
        assume_yes: Skip the Windows LLVM consent prompt.
        winget: The winget manager; it installs LLVM only with the user's consent.
        llvm_bases: The Windows LLVM install roots to look in.
        home: The home whose root holds the toolchains and vcpkg; the default home when ``None``.
        verifier: Checks the LLVM installer it downloads; the deprecated default slot's when ``None``.
        runner: Runs the git steps of the fetch; the provision runner on *console* when ``None``.
        pin: The commit the source must be at; the one the base fragment pins when ``None``.
    """
    console = console_or_default(console, "install_adaptivecpp")
    prefix = toolchains_dir(home=home) / "adaptivecpp"
    target = target_of(cfg)
    acpp = prefix / "bin" / target.acpp_launcher
    acpp_exe = prefix / "bin" / "acpp"
    for cand in (acpp, acpp_exe):
        if cand.is_file():
            console.info(f"AdaptiveCpp already present: {prefix}")
            return str(cand)

    # cmake/git may be off PATH (e.g. scoop), so honour the configured paths.
    find = which or shutil.which
    env = environ if environ is not None else os.environ
    cmake = cfg.expand(cfg.cmake_exe) if cfg.cmake_exe else (find("cmake") or "")
    git = find("git") or ""
    if not git or not cmake:
        console.warn("AdaptiveCpp build needs git and cmake; skipping.")
        return None

    if dry_run:
        console.info(f"(dry-run) would build AdaptiveCpp {ACPP_VERSION} -> {prefix}")
        return str(acpp_exe)

    llvm_dir, clang_prefix = LLVM_PLANS.plan_for(target, home=home, verifier=verifier).resolve(
        LlvmRequest(mgr=mgr, vcpkg=vcpkg, winget=winget, assume_yes=assume_yes,
                    llvm_bases=llvm_bases, console=console))
    if llvm_dir is None:
        _explain_acpp_skip(cfg, console)
        return None

    run_step = run_command or (
        lambda cmd, dry, *, check=False: run(cmd, dry, console=console, check=check))
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "acpp"
        build = src / "build"
        client = GitClient(git, runner or provision_runner(console), console=console)
        try:
            fetched = checkout_pinned(client, ACPP_URL, pin or base_git_pin(K_ACPP_PIN), src,
                                      dry_run)
        except CommitMismatchError as error:
            console.error(str(error))
            return None
        if not fetched:
            console.warn("AdaptiveCpp clone failed; skipping.")
            return None

        cfg_cmd = [
            cmake, "-S", str(src), "-B", str(build), "-G", "Ninja",
            "-DCMAKE_BUILD_TYPE=Release",
            f"-DCMAKE_INSTALL_PREFIX={prefix}",
            f"-DLLVM_DIR={llvm_dir}",
            "-DCMAKE_POLICY_VERSION_MINIMUM=3.5",
        ]
        if clang_prefix:
            cfg_cmd.append(f"-DCLANG_INSTALL_PREFIX={clang_prefix}")
            cfg_cmd.extend(target.acpp_configure_args(
                home_paths.root(home=home) / "vcpkg" / "scripts" / "buildsystems" / "vcpkg.cmake"))
        if cfg.ninja_exe:
            cfg_cmd.append(f"-DCMAKE_MAKE_PROGRAM={cfg.expand(cfg.ninja_exe)}")

        # clang-cl needs rc.exe (Windows SDK Resource Compiler) on PATH for the manifest embed.
        target.prepare_acpp_environment(env, lambda: _find_windows_sdk_rc_dir(glob))

        configure_ok = (configure or (lambda cmd, dry: _run_quiet(cmd, dry, console=console)))(
            cfg_cmd, dry_run)
        if not configure_ok:
            console.warn("AdaptiveCpp configure failed; skipping. "
                         "intel-llvm is installed and selected.")
            return None
        if run_step([cmake, "--build", str(build), "--target", "install"],
                dry_run, check=True) != 0:
            console.warn("AdaptiveCpp build failed; skipping. "
                         "intel-llvm is installed and selected.")
            return None

    result = next((c for c in (acpp, acpp_exe) if c.is_file()), None)
    if result:
        console.success(f"AdaptiveCpp installed: {prefix}")
        return str(result)
    console.warn("AdaptiveCpp build completed but acpp binary not found.")
    return None


def _explain_acpp_skip(cfg: "ProvisionConfig", console: Any) -> None:
    """Explain why the acpp build was skipped and how to enable it later.

    Args:
        cfg: Resolved configuration; selects the platform-specific message.
        console: The console the explanation is printed through.
    """
    console.warn("AdaptiveCpp (acpp) was skipped — it builds from source and its "
                 "LLVM development dependency is not available.")
    for note in target_of(cfg).acpp_skip_notes(LLVM_WINDOWS_VERSION):
        console.info(note)
    console.info("This is non-fatal: intel-llvm is installed and selected, so you "
                 "can build and run now. acpp is the secondary toolchain.")
