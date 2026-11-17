# probe.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tool-path probing shared by every provisioning CLI."""

from __future__ import annotations

import glob
import logging
import os
import shutil
from pathlib import Path
from typing import Callable, Sequence

from sushicore.proc import CommandRunner, did_not_run
from sushicore.provision import home
from sushicore.provision.config import ProvisionConfig
from sushicore.provision.host import IHost, current_host
from sushicore.provision.process_run import provision_runner
from sushicore.provision.probe_plan import PROBE_PLANS
from sushicore.provision.target import target_of

_log = logging.getLogger(__name__)

_VS_EDITIONS = ("BuildTools", "Community", "Professional", "Enterprise")
_VCVARS_REL = Path("VC") / "Auxiliary" / "Build" / "vcvars64.bat"
K_ICX_GLOBS = [
    r"C:/Program Files (x86)/Intel/oneAPI/compiler/*/bin/icx-cl.exe",
    r"C:/Program Files/Intel/oneAPI/compiler/*/bin/icx-cl.exe",
]
K_RC_GLOBS = [
    r"C:/Program Files (x86)/Windows Kits/10/bin/*/x64/rc.exe",
    r"C:/Program Files/Windows Kits/10/bin/*/x64/rc.exe",
]
# Neither the apt CUDA toolkit nor oneAPI add themselves to PATH, so these well-known install locations are checked directly.
K_NVCC_GLOBS_LINUX = [
    "/usr/local/cuda/bin/nvcc",
    "/usr/local/cuda-*/bin/nvcc",
]
K_ICX_GLOBS_LINUX = [
    "/opt/intel/oneapi/compiler/*/bin/icpx",
    "/opt/intel/oneapi/compiler/*/bin/icx",
]


def first_glob_match(patterns: list[str]) -> str:
    """Return the last (highest-sorting) match among *patterns*, or ''."""
    for pat in patterns:
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[-1]  # latest version when sorted
    return ""


def first_existing(paths: list[str]) -> str:
    """Return the first path in *paths* that exists, or ''."""
    for p in paths:
        if Path(p).exists():
            return p
    return ""


def _vcvars_from_vswhere(program_files: str | None = None,
                         runner: CommandRunner | None = None) -> Path | None:
    """Return the vcvars64.bat of the latest VS install vswhere reports, or None.

    Args:
        program_files: The folder holding ``Microsoft Visual Studio``; the environment's when ``None``.
        runner: Runs vswhere; the provision runner when ``None``.
    """
    program_files = program_files or os.environ.get("ProgramFiles(x86)") or os.environ.get(
        "ProgramFiles", r"C:\Program Files")
    vswhere = Path(program_files) / "Microsoft Visual Studio" / "Installer" / "vswhere.exe"
    if not vswhere.is_file():
        return None
    cmd = [str(vswhere), "-latest", "-prerelease", "-products", "*",
           "-requires", "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
           "-property", "installationPath"]
    code, out, err = (runner or provision_runner()).capture(cmd, timeout=30)
    if did_not_run(cmd[0], code, err):
        _log.warning("vswhere did not run (%s); no Visual Studio install is reported", err)
        return None
    if code != 0:
        _log.warning("vswhere exited with status %d; no Visual Studio install is reported", code)
        return None
    for line in out.splitlines():
        candidate = Path(line.strip()) / _VCVARS_REL
        if line.strip() and candidate.is_file():
            return candidate
    return None


def _vcvars_from_disk_scan(program_files: Sequence[Path] | None = None) -> Path | None:
    """Return the first vcvars64.bat under the Program Files VS roots, newest year first.

    Args:
        program_files: The folders holding ``Microsoft Visual Studio``; the environment's when ``None``.
    """
    if program_files is None:
        program_files = [Path(os.environ[var]) for var in ("ProgramFiles", "ProgramFiles(x86)")
                         if os.environ.get(var)]
    roots = [folder / "Microsoft Visual Studio" for folder in program_files]
    for root in roots:
        if not root.is_dir():
            continue
        years = sorted((d for d in root.iterdir() if d.is_dir()),
                       key=lambda d: d.name, reverse=True)
        for year in years:
            for edition in _VS_EDITIONS:
                candidate = year / edition / _VCVARS_REL
                if candidate.is_file():
                    return candidate
    return None


def find_vcvars(host: IHost | None = None,
                vswhere: Callable[[], Path | None] | None = None,
                program_files: Sequence[Path] | None = None) -> Path | None:
    """Return the vcvars64.bat of an installed Visual Studio, or None off Windows.

    Args:
        host: The host to judge; the running one when ``None``.
        vswhere: Gives the install vswhere reports; asks vswhere when ``None``.
        program_files: The folders the disk scan reads; the environment's when ``None``.
    """
    if not (host or current_host()).hosts_visual_studio:
        return None
    return (vswhere or _vcvars_from_vswhere)() or _vcvars_from_disk_scan(program_files)


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


def detect_gpu_vendor() -> str:
    """Best-effort discrete-GPU vendor detection: nvidia | amd | intel | none.

    Vendor management tools answer first when present. Otherwise the display
    adapters this operating system reports are classified, so a fresh machine
    with no vendor stack installed is still recognised. Returns ``none`` when
    nothing recognisable is found; the caller then provisions only the CPU
    (SPIR/OpenCL) path.
    """
    if shutil.which("nvidia-smi"):
        return "nvidia"
    if shutil.which("rocminfo") or shutil.which("rocm-smi"):
        return "amd"
    return classify_display_adapters(current_host().display_adapters(provision_runner()))


#: Name fragments, without spaces or hyphens, that mark an AMD or Intel adapter as integrated.
_INTEGRATED_MARKERS = (
    "radeon(tm)graphics", "radeongraphics", "radeonvega", "vegaseries", "vegamobile",
    "610m", "660m", "680m", "740m", "760m", "780m", "880m", "890m",
    "raven", "picasso", "renoir", "lucienne", "cezanne", "barcelo", "rembrandt",
    "mendocino", "phoenix", "hawkpoint", "raphael", "graniteridge", "strix",
    "uhdgraphics", "hdgraphics", "iris", "alderlake", "raptorlake", "meteorlake",
    "lunarlake", "arrowlake", "tigerlake", "cometlake", "coffeelake", "arc(tm)graphics",
)
#: Name fragments, without spaces or hyphens, that mark an adapter as discrete over any integrated marker.
_DISCRETE_MARKERS = (
    "nvidia", "radeonrx", "rxvega", "radeonpro", "firepro", "instinct", "navi",
    "arc(tm)a", "arc(tm)b", "[arca", "[arcb", "dg1", "dg2", "battlemage", "irisxemax",
)

#: Vendor keys in preference order, each with the name fragments that identify it.
_VENDOR_MARKERS = (
    ("nvidia", ("nvidia",)),
    ("amd", ("advancedmicrodevices", "amd/ati", "radeon")),
    ("intel", ("intel",)),
)


def _normalise_adapter(line: str) -> str:
    """Return a display-adapter line lower-cased with its spaces and hyphens removed."""
    return line.lower().replace(" ", "").replace("-", "")


def is_integrated_adapter(line: str) -> bool:
    """Return True when one display-adapter line names an integrated GPU."""
    name = _normalise_adapter(line)
    if any(marker in name for marker in _DISCRETE_MARKERS):
        return False
    return any(marker in name for marker in _INTEGRATED_MARKERS)


def _adapter_vendor(line: str) -> str | None:
    """Return the vendor key one display-adapter line names, or None."""
    name = _normalise_adapter(line)
    for vendor, markers in _VENDOR_MARKERS:
        if any(marker in name for marker in markers):
            return vendor
    return None


def classify_display_adapters(adapters: str) -> str:
    """Return the vendor to provision for display-adapter text, or ``none`` when no vendor is known.

    A discrete adapter is preferred over an integrated one; within each group the
    order is NVIDIA, AMD, Intel.
    """
    ranked = [(is_integrated_adapter(line), rank, vendor)
              for line in adapters.splitlines()
              for rank, (vendor, _markers) in enumerate(_VENDOR_MARKERS)
              if _adapter_vendor(line) == vendor]
    return min(ranked)[2] if ranked else "none"


def binary_works(cmd: str, runner: CommandRunner | None = None) -> bool:
    """Return True only if *cmd* is on PATH (or an absolute path) and runs cleanly.

    Tries --version first; falls back to -version for tools that use that flag.
    A missing binary, a crash, or a non-zero exit all return False.

    Args:
        runner: Runs the command; the provision runner when ``None``.
    """
    run = runner or provision_runner()
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
