# toolchain_identity.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Names the SYCL compiler a build uses, so a package built with another one is never reused."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Callable

from ..toolchains.stamp import read_toolchain_stamp
from .package_error import PackageError

#: Runs a command and returns its exit code and standard output.
Probe = Callable[[list[str]], tuple[int, str]]


def run_probe(command: list[str]) -> tuple[int, str]:
    """Run *command*; return its exit code and its standard output.

    Raises:
        PackageError: The command cannot start or times out.
    """
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as exc:
        raise PackageError(f"cannot run {command[0]}: {exc}") from exc
    return result.returncode, result.stdout


def compiler_identity(compiler: str, probe: Probe = run_probe) -> str:
    """Return the identity of *compiler*: its ``--version`` hash, plus its toolchain tag.

    The tag is read from the stamp of the install folder that holds ``bin/<compiler>``, when it
    has one. The version output alone separates two nightlies of one toolchain.

    Args:
        compiler: The compiler path.
        probe: Runs a command; replaced in tests.

    Raises:
        PackageError: The compiler does not run, or prints nothing.
    """
    code, output = probe([compiler, "--version"])
    if code != 0 or not output.strip():
        raise PackageError(
            f"{compiler} --version gave no identity (exit {code}); a package key built on it "
            "would be a guess.")
    identity = hashlib.sha256(output.encode("utf-8")).hexdigest()[:16]
    tag = str(read_toolchain_stamp(Path(compiler).resolve().parent.parent).get("tag") or "")
    return f"{identity}:{tag}" if tag else identity
