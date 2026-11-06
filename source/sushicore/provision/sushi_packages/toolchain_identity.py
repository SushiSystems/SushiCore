# toolchain_identity.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Names the SYCL compiler a build uses, so a package built with another one is never reused."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Any, Callable, Mapping

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


#: Reads the toolchain stamp of an install folder; an install with none reads as empty.
ReadStamp = Callable[[Path], Mapping[str, Any]]


class MemoryProbe:
    """Answers the exit code and the output set for a compiler, and runs nothing.

    Args:
        answers: The ``(exit code, standard output)`` to answer, by compiler path.

    Attributes:
        calls: Every command asked, in order.
    """

    def __init__(self, answers: Mapping[str, tuple[int, str]]) -> None:
        """Keep *answers*; no command has been asked yet."""
        self._answers = dict(answers)
        self.calls: list[list[str]] = []

    def __call__(self, command: list[str]) -> tuple[int, str]:
        """Record *command* and return the answer set for its executable.

        Raises:
            KeyError: No answer was set for ``command[0]``.
        """
        self.calls.append(list(command))
        return self._answers[command[0]]


class MemoryIdentity:
    """Names every compiler with one identity and counts how often it was asked.

    Args:
        identity: What every compiler is named.

    Attributes:
        asked: The compiler path of every call, in order.
    """

    def __init__(self, identity: str = "tc") -> None:
        """Keep *identity*; nothing has been asked yet."""
        self._identity = identity
        self.asked: list[str] = []

    def __call__(self, compiler: str) -> str:
        """Record *compiler* and return the identity."""
        self.asked.append(compiler)
        return self._identity


def compiler_identity(compiler: str, probe: Probe = run_probe,
                      read_stamp: ReadStamp | None = None) -> str:
    """Return the identity of *compiler*: its ``--version`` hash, plus its toolchain tag.

    The tag is read from the stamp of the install folder that holds ``bin/<compiler>``, when it
    has one. The version output alone separates two nightlies of one toolchain.

    Args:
        compiler: The compiler path.
        probe: Runs a command; replaced in tests.
        read_stamp: Reads the stamp of an install folder; :func:`read_toolchain_stamp` when
            None. It is looked up when the function runs, so a test can replace it.

    Raises:
        PackageError: The compiler does not run, or prints nothing.
    """
    code, output = probe([compiler, "--version"])
    if code != 0 or not output.strip():
        raise PackageError(
            f"{compiler} --version gave no identity (exit {code}); a package key built on it "
            "would be a guess.")
    identity = hashlib.sha256(output.encode("utf-8")).hexdigest()[:16]
    reader = read_toolchain_stamp if read_stamp is None else read_stamp
    tag = str(reader(Path(compiler).resolve().parent.parent).get("tag") or "")
    return f"{identity}:{tag}" if tag else identity
