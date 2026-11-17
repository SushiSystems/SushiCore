# probe.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Finds the SYCL and CUDA toolchains of this machine and checks that their binaries run.

The GPU vendor and Visual Studio finders are re-exported for the module CLIs that import them here.
"""

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from typing import Callable, Sequence

from sushicore.proc import CommandRunner, did_not_run
from sushicore.provision import home
from sushicore.provision.config import ProvisionConfig
from sushicore.provision.glob_search import K_ICX_GLOBS, K_ICX_GLOBS_LINUX, K_NVCC_GLOBS_LINUX, first_glob_match
from sushicore.provision.gpu_vendor import classify_display_adapters, detect_gpu_vendor  # noqa: F401
from sushicore.provision.probe_plan import PROBE_PLANS
from sushicore.provision.target import target_of
from sushicore.provision.vs_locator import find_vcvars  # noqa: F401
from sushicore.quiet_runner import quiet_runner

_log = logging.getLogger(__name__)


def _toolchains_dir() -> Path:
    """Where a provisioning CLI installs the intel-llvm bundle and AdaptiveCpp."""
    return home.toolchains_dir()


def installed_toolchain(name: str, relative: Path, roots: Sequence[Path] | None = None,
                        is_file: Callable[[Path], bool] | None = None) -> Path | None:
    """Return the first ``toolchains/<name>/<relative>`` file across the dependency roots.

    Args:
        roots: The roots to look through, in order; the search roots when ``None``.
        is_file: Asked whether a candidate is a file; ``Path.is_file`` when ``None``.
    """
    present = is_file or Path.is_file
    for root in (home.search_roots() if roots is None else roots):
        candidate = root / "toolchains" / name / relative
        if present(candidate):
            return candidate
    return None


def _installed_clang(cfg: ProvisionConfig) -> Path | None:
    """Return the intel/llvm bundle's clang++ in any dependency root, or None."""
    return installed_toolchain("llvm-sycl", Path("bin") / target_of(cfg).clang_executable)


def _installed_acpp() -> Path | None:
    """Return the AdaptiveCpp launcher in any dependency root, or None."""
    for name in ("acpp.bat", "acpp"):
        found = installed_toolchain("adaptivecpp", Path("bin") / name)
        if found is not None:
            return found
    return None


def discover_installed_toolchains(cfg: ProvisionConfig, values: dict[str, str]) -> None:
    """Record the paths of toolchains installed by the provisioning CLI, if present."""
    clang = _installed_clang(cfg)
    if clang is not None:
        values["llvm_root"] = str(clang.parents[1])
    acpp = _installed_acpp()
    if acpp is not None:
        values["acpp_exe"] = str(acpp)


def toolchain_status(cfg: ProvisionConfig, gpu: bool) -> list[tuple[str, bool, str]]:
    """Return one ``(name, present, detail)`` row per SYCL toolchain (and CUDA if *gpu*)."""
    target = target_of(cfg)

    found_clang = _installed_clang(cfg)
    clang = found_clang or _toolchains_dir() / "llvm-sycl" / "bin" / target.clang_executable
    intel_ok = found_clang is not None and binary_works(str(clang))

    found_acpp = _installed_acpp()
    acpp_path = str(found_acpp) if found_acpp is not None else ""
    acpp_ok = bool(acpp_path) and binary_works(acpp_path)

    # oneAPI is system-wide; reuse the active-compiler probe. See source/sushicore/provision/README.md.
    active, _ = find_sycl_compiler(cfg)
    oneapi_bin = (first_glob_match(K_ICX_GLOBS) or shutil.which("icx-cl")
                  or shutil.which("icpx") or shutil.which("icx")
                  or (first_glob_match(K_ICX_GLOBS_LINUX) if target.searches_system_prefixes else ""))
    oneapi_ok = (active in ("icx-cl", "icpx")
                 or (bool(oneapi_bin) and binary_works(oneapi_bin)))

    # A path in square brackets would otherwise be parsed as rich markup.
    from rich.markup import escape as _rich_escape

    rows = [
        ("intel-llvm",  intel_ok, f"intel/llvm SYCL toolchain (clang++ -fsycl) -> {_rich_escape(str(clang))}" if intel_ok else "intel/llvm SYCL toolchain (clang++ -fsycl)"),
        ("adaptivecpp", acpp_ok,  f"AdaptiveCpp (acpp) -> {_rich_escape(acpp_path)}" if acpp_ok else "AdaptiveCpp (acpp)"),
        ("oneapi",      oneapi_ok, f"Intel oneAPI DPC++ (icx/icpx) -> {_rich_escape(oneapi_bin)}" if oneapi_ok and oneapi_bin else "Intel oneAPI DPC++ (icx/icpx)"),
    ]
    if gpu:
        cuda_path = os.environ.get("CUDA_PATH", "")
        in_cuda_path = (os.path.join(cuda_path, "bin", target.nvcc_executable)
                        if cuda_path else "")
        nvcc_bin = ((in_cuda_path if in_cuda_path and os.path.isfile(in_cuda_path) else "")
                    or shutil.which("nvcc")
                    or (first_glob_match(K_NVCC_GLOBS_LINUX) if target.searches_system_prefixes else ""))
        nvcc_ok = bool(nvcc_bin) and binary_works(nvcc_bin)
        detail = (f"NVIDIA CUDA toolkit (nvcc) -> {_rich_escape(nvcc_bin)}" if nvcc_ok
                  else "NVIDIA CUDA toolkit (nvcc)")
        rows.append(("cuda", nvcc_ok, detail))
    return rows


def binary_works(cmd: str, runner: CommandRunner | None = None) -> bool:
    """Return True only if *cmd* is on PATH (or an absolute path) and runs cleanly.

    Tries --version first; falls back to -version for tools that use that flag.
    A missing binary, a crash, or a non-zero exit all return False.

    Args:
        runner: Runs the command; the quiet runner when ``None``.
    """
    run = runner or quiet_runner()
    for flag in ("--version", "-version"):
        code, _out, err = run.capture([cmd, flag], timeout=15)
        if did_not_run(cmd, code, err):
            _log.debug("%s did not run (%s); it is reported as not working", cmd, err)
            return False
        if code == 0:
            return True
    return False


def find_sycl_compiler(cfg: ProvisionConfig) -> tuple[str | None, str]:
    """Return (compiler, location) for the active SYCL toolchain, or (None, '').

    Existence of the binary is not enough — a partial install can leave the exe
    on disk with missing DLLs. The binary is verified by running --version.
    """
    return PROBE_PLANS.plan_for(target_of(cfg)).find_sycl_compiler(cfg)


def find_configured_toolchain(cfg: ProvisionConfig) -> tuple[str | None, str]:
    """Return (label, path) for a SYCL compiler installed by the provisioning CLI, or (None, '')."""
    clang_executable = target_of(cfg).clang_executable
    base = _toolchains_dir()

    bundle = ""
    if cfg.llvm_root:
        cand = Path(cfg.expand(cfg.llvm_root)) / "bin" / clang_executable
        if cand.is_file():
            bundle = str(cand)
    if not bundle:
        cand = base / "llvm-sycl" / "bin" / clang_executable
        if cand.is_file():
            bundle = str(cand)
    if bundle and binary_works(bundle):
        return ("intel-llvm clang++", bundle)

    acpp = cfg.expand(cfg.acpp_exe) if cfg.acpp_exe else ""
    if not (acpp and Path(acpp).is_file()):
        for name in ("acpp.bat", "acpp"):
            cand = base / "adaptivecpp" / "bin" / name
            if cand.is_file():
                acpp = str(cand)
                break
    if acpp and Path(acpp).is_file() and binary_works(acpp):
        return ("acpp", acpp)

    return (None, "")


def resolve_local_config(cfg: ProvisionConfig, gpu: bool = False) -> dict[str, str]:
    """Probe machine-specific tool paths to write into ``[tool.<platform>]``.

    Returns only the fields that were actually found, so we never write empty
    placeholders that would shadow the committed defaults.
    """
    return PROBE_PLANS.plan_for(target_of(cfg)).resolve_local_config(cfg)


def toolchain_presence(cfg: "ProvisionConfig") -> dict[str, bool]:
    """Return each SYCL toolchain's key mapped to whether this machine holds it."""
    return {name: present for name, present, _detail in toolchain_status(cfg, False)}
