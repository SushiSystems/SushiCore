# cuda_hardware.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""What the NVIDIA driver reports about this machine: each card's architecture and the newest
CUDA release the driver can run."""

from __future__ import annotations

import dataclasses
import logging
import re
import typing

from ...proc import CommandRunner
from ...quiet_runner import quiet_runner

_log = logging.getLogger(__name__)

#: The banner line ``nvidia-smi`` prints with the newest CUDA release the driver runs.
K_DRIVER_CUDA = re.compile(r"CUDA Version:\s*(\d+)\.(\d+)")

#: One ``compute_cap`` row, such as ``8.9``.
K_COMPUTE_CAP = re.compile(r"^(\d+)\.(\d+)$")

#: Seconds each ``nvidia-smi`` query may take.
K_QUERY_TIMEOUT = 60


@typing.final
@dataclasses.dataclass(frozen=True, slots=True)
class NvidiaHardware:
    """The NVIDIA cards of a machine, as the driver reports them.

    Args:
        architectures: Each distinct compute capability as nvcc spells it without the
            prefix, sorted: ``("61", "89")``.
        driver_cuda: The newest CUDA ``(major, minor)`` the installed driver runs.
    """

    architectures: tuple[str, ...]
    driver_cuda: tuple[int, int]

    def describe(self) -> str:
        """Return the cards and the ceiling for a console line."""
        major, minor = self.driver_cuda
        return (f"{', '.join(f'sm_{arch}' for arch in self.architectures)} "
                f"(the driver runs CUDA up to {major}.{minor})")

    def fingerprint(self) -> str:
        """Return a stable text that changes when a card or the driver's CUDA ceiling does."""
        major, minor = self.driver_cuda
        return f"sm={','.join(self.architectures)};driver={major}.{minor}"


def parse_hardware(compute_caps: str, banner: str) -> NvidiaHardware | None:
    """Build the hardware record from ``nvidia-smi`` output, or None when either part is missing.

    Args:
        compute_caps: The output of ``nvidia-smi --query-gpu=compute_cap --format=csv,noheader``.
        banner: The output of a bare ``nvidia-smi``.
    """
    architectures = sorted({f"{m.group(1)}{m.group(2)}"
                            for m in (K_COMPUTE_CAP.match(line.strip())
                                      for line in compute_caps.splitlines()) if m},
                           key=int)
    driver = K_DRIVER_CUDA.search(banner)
    if not architectures or driver is None:
        return None
    return NvidiaHardware(tuple(architectures), (int(driver.group(1)), int(driver.group(2))))


def query_hardware(runner: CommandRunner | None = None) -> NvidiaHardware | None:
    """Ask ``nvidia-smi`` about this machine; None when there is no driver to ask.

    Args:
        runner: Runs ``nvidia-smi``; the quiet runner when ``None``.
    """
    run = runner or quiet_runner()
    caps = _ask(run, ["nvidia-smi", "--query-gpu=compute_cap", "--format=csv,noheader"])
    banner = _ask(run, ["nvidia-smi"]) if caps is not None else None
    if caps is None or banner is None:
        return None
    return parse_hardware(caps, banner)


def _ask(runner: CommandRunner, command: list[str]) -> str | None:
    """Return the standard output of *command*, or None when it did not exit zero in time."""
    code, out, err = runner.capture(command, timeout=K_QUERY_TIMEOUT)
    if code != 0:
        _log.info("nvidia-smi did not answer (exit %d: %s)", code, err.strip())
        return None
    return out
