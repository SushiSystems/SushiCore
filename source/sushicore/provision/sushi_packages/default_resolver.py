# default_resolver.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Assembles the package resolver a CLI runs, from the real git, CLI processes and store."""

from __future__ import annotations

import importlib.metadata
import os
from typing import Callable, Mapping

from .. import home
from .closure_walk import ClosureWalk
from .compiler_check import CompilerCheck
from .configure_inputs import ConfigureInputs, probe_cmake_version
from .forced_packages import ForcedPackages
from .key_factory import KeyFactory
from .link_publisher import LinkPublisher
from .package_builder import CliPackageBuilder, Run, run_process
from .package_environment import PackageEnvironment
from .package_error import PackageError
from .package_locks import PackageLocks
from .package_resolver import PackageResolver
from .package_store import K_DEFAULT_KEEP, PackageStore
from .source_locator import SushiSourceLocator
from .source_state import GitSourceInspector
from .stable_link import StableLink
from .toolchain_identity import compiler_identity

#: The environment variable that overrides the configured keep count.
K_KEEP_VARIABLE = "SUSHISTACK_PACKAGE_KEEP"

#: What the version reads as when the package metadata is absent, such as in a source tree.
K_UNKNOWN_VERSION = "unknown"


def sushicore_version() -> str:
    """Return the installed SushiCore version, or :data:`K_UNKNOWN_VERSION`."""
    try:
        return importlib.metadata.version("sushicore")
    except importlib.metadata.PackageNotFoundError:
        return K_UNKNOWN_VERSION


def effective_keep(configured: int, env: Mapping[str, str]) -> int:
    """Return how many packages of a library to keep: the environment's, else *configured*.

    Raises:
        PackageError: The variable is not a whole number, or the result is below 1.
    """
    text = env.get(K_KEEP_VARIABLE, "")
    if not text:
        return configured if configured else K_DEFAULT_KEEP
    try:
        keep = int(text)
    except ValueError as exc:
        raise PackageError(f"{K_KEEP_VARIABLE} is {text!r}, and it is a whole number.") from exc
    if keep < 1:
        raise PackageError(f"{K_KEEP_VARIABLE} is {keep}; the store keeps at least one package.")
    return keep


def default_resolver(keep: int, report: Callable[[str], None], warn: Callable[[str], None],
                     env: Mapping[str, str] | None = None, cmake: str = "cmake",
                     run: Run = run_process) -> PackageResolver:
    """Return the resolver over ``<home>/packages`` that starts git and the library CLIs.

    No process starts until :meth:`PackageResolver.resolve` runs.

    Args:
        keep: How many packages of a library the store keeps.
        report: Receives one line per library.
        warn: Receives the warnings.
        env: The environment of the CLI; ``os.environ`` when None.
        cmake: The cmake executable the key's CMake version is read from.
        run: Runs a library CLI command.
    """
    environment = os.environ if env is None else env
    root = home.root() / "packages"
    store = PackageStore(root, effective_keep(keep, environment), warn=warn)
    locks = PackageLocks(root)
    keys = KeyFactory(GitSourceInspector(),
                      ConfigureInputs(lambda: probe_cmake_version(cmake)),
                      compiler_identity, sushicore_version())
    builder = CliPackageBuilder(run, CompilerCheck(warn=warn), PackageEnvironment(environment))
    return PackageResolver(
        ClosureWalk(SushiSourceLocator()), keys, store, builder,
        ForcedPackages(environment, store, warn), locks,
        LinkPublisher(locks, StableLink(root)), report)
