# cuda_hardware.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""What the NVIDIA driver reports about this machine: each card's architecture and the newest
CUDA release the driver can run."""

from __future__ import annotations

import dataclasses
import logging
import re
import shutil
import subprocess
import typing

_log = logging.getLogger(__name__)

#: The banner line ``nvidia-smi`` prints with the newest CUDA release the driver runs.
K_DRIVER_CUDA = re.compile(r"CUDA Version:\s*(\d+)\.(\d+)")

#: One ``compute_cap`` row, such as ``8.9``.
K_COMPUTE_CAP = re.compile(r"^(\d+)\.(\d+)$")


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


def query_hardware(run: typing.Callable[[list[str]], str] | None = None) -> NvidiaHardware | None:
    """Ask ``nvidia-smi`` about this machine; None when there is no driver to ask.

    Args:
        run: Runs a command and returns its standard output; raises ``OSError`` or
            ``subprocess.SubprocessError`` on failure. Defaults to a real subprocess.
    """
    runner = run or _run
    try:
        caps = runner(["nvidia-smi", "--query-gpu=compute_cap", "--format=csv,noheader"])
        banner = runner(["nvidia-smi"])
    except (OSError, subprocess.SubprocessError) as error:
        _log.info("nvidia-smi did not answer (%s: %s)", type(error).__name__, error)
        return None
    return parse_hardware(caps, banner)


def _run(command: list[str]) -> str:
    """Run *command* and return its standard output."""
    exe = shutil.which(command[0])
    if exe is None:
        raise FileNotFoundError(command[0])
    done = subprocess.run([exe, *command[1:]], capture_output=True, text=True, check=True,
                          timeout=60)
    return done.stdout
