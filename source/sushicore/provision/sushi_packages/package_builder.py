# package_builder.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Builds and installs one Sushi library through the library's own CLI."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Protocol

from .build_tree import BuildTree
from .compiler_check import CompilerCheck
from .package_environment import PackageEnvironment
from .package_error import PackageError
from .package_key import PackageKey

#: The folder of the library's builds; a package tree lives below it.
K_BUILD_FOLDER = "build"


class Run(Protocol):
    """Runs a command in a folder with an environment and returns its exit code."""

    def __call__(self, command: list[str], cwd: Path, env: Mapping[str, str]) -> int:
        """Run *command*; return its exit code."""


def run_process(command: list[str], cwd: Path, env: Mapping[str, str]) -> int:
    """Run *command* in *cwd* with *env*; return its exit code.

    Raises:
        PackageError: The command cannot start.
    """
    try:
        return subprocess.run(command, cwd=cwd, env=dict(env)).returncode
    except OSError as exc:
        raise PackageError(f"cannot run {command[0]}: {exc}") from exc


@dataclass(frozen=True, slots=True)
class BuildRequest:
    """What one library build needs."""

    key: PackageKey
    checkout: Path
    #: The library's CLI command, such as ``sr``.
    cli: str
    #: Where the install goes: the staged prefix.
    prefix: Path
    #: The compiler the consumer builds with.
    compiler: str
    #: The install prefix of each package already chosen below the library, by name.
    below: Mapping[str, Path] = field(default_factory=dict)


class IPackageBuilder(Protocol):
    """Builds the package a request names into the request's prefix."""

    def build(self, request: BuildRequest) -> None:
        """Build and install; raise :class:`PackageError` on failure."""


class CliPackageBuilder:
    """Runs ``<cli> build`` then ``<cli> package`` in the library's checkout."""

    def __init__(self, run: Run, check: CompilerCheck, environment: PackageEnvironment) -> None:
        """Bind the builder to what touches the machine.

        Args:
            run: Runs a command.
            check: Compares the compiler of the build tree with the key's.
            environment: Assembles the environment of the build.
        """
        self._run = run
        self._check = check
        self._environment = environment

    def build(self, request: BuildRequest) -> None:
        """Check the tree, build, check the tree again, then install.

        Raises:
            PackageError: A command fails, or the build tree was made with another compiler.
        """
        key = request.key
        tree = BuildTree(key.build_type, key.options, key.toolchain)
        relative = f"{K_BUILD_FOLDER}/{tree.folder}"
        folder = request.checkout / K_BUILD_FOLDER / tree.folder
        env = self._environment.assemble(request.compiler, request.below)
        self._check.verify(folder, key.toolchain)
        self._step([request.cli, "build", "--type", key.build_type, "--build-dir", relative,
                    "--lean", *key.options], request, env)
        self._check.verify(folder, key.toolchain)
        self._step([request.cli, "package", "--build-dir", relative, "--prefix",
                    str(request.prefix), "--no-archive", "--force"], request, env)

    def _step(self, command: list[str], request: BuildRequest, env: Mapping[str, str]) -> None:
        """Run one command of the build; raise when it exits non-zero."""
        code = self._run(command, request.checkout, env)
        if code != 0:
            raise PackageError(
                f"`{' '.join(command)}` failed with exit {code} in {request.checkout}.")
