# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Wiring every registered GPU backend's adapter build into one install run."""

from __future__ import annotations

import typing
from pathlib import Path

from .._output import console
from .compiler_identity import read_intel_llvm_commit

if typing.TYPE_CHECKING:
    from ..config import ProvisionConfig
    from .adapter_builder import AdapterBuilder
    from .backend import ToolkitInstall
    from .registry import Registry


def _clang_path(toolchain_root: Path, cfg: "ProvisionConfig") -> Path:
    """Return the compiler binary whose commit identifies the installed bundle."""
    name = "clang++.exe" if cfg.is_windows else "clang++"
    return toolchain_root / "bin" / name


def provision_gpu_adapters(
    cfg: "ProvisionConfig",
    registry: "Registry",
    toolchain_root: Path,
    builder: "AdapterBuilder",
    dry_run: bool,
    commit_reader: typing.Callable[[Path], str | None] = read_intel_llvm_commit,
) -> None:
    """Build every located backend's Unified Runtime adapter for one toolchain.

    Reads the intel/llvm commit the toolchain at *toolchain_root* was built
    from, then asks each registered backend's locator whether its toolkit is
    present. A present toolkit gets its adapter built through *builder*; an
    absent one is reported and skipped.

    :param cfg: Resolved configuration; selects the platform's compiler name.
    :param registry: The backends to provision, in report order.
    :param toolchain_root: Root of the installed SYCL toolchain (holds ``bin/``).
    :param builder: Builds one backend's adapter for one compiler commit.
    :param dry_run: Report the action without touching the filesystem.
    :param commit_reader: Injected in place of :func:`read_intel_llvm_commit`
        for tests.
    """
    try:
        _provision(cfg, registry, toolchain_root, builder, dry_run, commit_reader)
    except Exception as exc:
        console.warn(f"GPU adapter provisioning failed ({type(exc).__name__}): {exc}")


def _provision(
    cfg: "ProvisionConfig",
    registry: "Registry",
    toolchain_root: Path,
    builder: "AdapterBuilder",
    dry_run: bool,
    commit_reader: typing.Callable[[Path], str | None],
) -> None:
    """Run the provisioning steps proper, with recoverable errors left to the caller."""
    commit = commit_reader(_clang_path(toolchain_root, cfg))
    if commit is None:
        if dry_run:
            console.info("(dry-run) would read the compiler commit and build GPU adapters.")
        else:
            console.warn(
                "Could not read the intel/llvm commit the installed SYCL toolchain "
                "was built from; skipping every GPU adapter build.")
        return

    for spec in registry.all():
        install: "ToolkitInstall | None" = spec.locator.locate(cfg)
        if install is None:
            console.info(f"{spec.vendor} toolkit not found; adapter build skipped.")
            continue
        builder.build(spec, install, toolchain_root, commit, dry_run)
