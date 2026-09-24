# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Tool-path probing shared by every provisioning CLI."""

from __future__ import annotations

import glob
import os
import shutil
import subprocess
import sys
from pathlib import Path

from sushicore.provision import home
from sushicore.provision.config import ProvisionConfig

# Common Windows install roots probed when a tool is not already on PATH.
_VS_VCVARS_GLOBS = [
    r"C:/Program Files/Microsoft Visual Studio/2022/*/VC/Auxiliary/Build/vcvars64.bat",
    r"C:/Program Files (x86)/Microsoft Visual Studio/2022/*/VC/Auxiliary/Build/vcvars64.bat",
]
_VS_EDITIONS = ("BuildTools", "Community", "Professional", "Enterprise")
_VCVARS_REL = Path("VC") / "Auxiliary" / "Build" / "vcvars64.bat"
_ONEAPI_ROOTS = [
    r"C:/Program Files (x86)/Intel/oneAPI",
    r"C:/Program Files/Intel/oneAPI",
]
_ICX_GLOBS = [
    r"C:/Program Files (x86)/Intel/oneAPI/compiler/*/bin/icx-cl.exe",
    r"C:/Program Files/Intel/oneAPI/compiler/*/bin/icx-cl.exe",
]
_RC_GLOBS = [
    r"C:/Program Files (x86)/Windows Kits/10/bin/*/x64/rc.exe",
    r"C:/Program Files/Windows Kits/10/bin/*/x64/rc.exe",
]
# Neither the apt CUDA toolkit nor oneAPI add themselves to PATH, so these well-known install locations are checked directly.
_NVCC_GLOBS_LINUX = [
    "/usr/local/cuda/bin/nvcc",
    "/usr/local/cuda-*/bin/nvcc",
]
_ICX_GLOBS_LINUX = [
    "/opt/intel/oneapi/compiler/*/bin/icpx",
    "/opt/intel/oneapi/compiler/*/bin/icx",
]


def _first_glob(patterns: list[str]) -> str:
    """Return the last (highest-sorting) match among *patterns*, or ''."""
    for pat in patterns:
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[-1]  # latest version when sorted
    return ""


def _first_existing(paths: list[str]) -> str:
    """Return the first path in *paths* that exists, or ''."""
    for p in paths:
        if Path(p).exists():
            return p
    return ""


def _vcvars_from_vswhere() -> Path | None:
    """Return the vcvars64.bat of the latest VS install vswhere reports, or None."""
    program_files = os.environ.get("ProgramFiles(x86)") or os.environ.get(
        "ProgramFiles", r"C:\Program Files")
    vswhere = Path(program_files) / "Microsoft Visual Studio" / "Installer" / "vswhere.exe"
    if not vswhere.is_file():
        return None
    cmd = [str(vswhere), "-latest", "-prerelease", "-products", "*",
           "-requires", "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
           "-property", "installationPath"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, errors="replace",
                                timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    for line in result.stdout.splitlines():
        candidate = Path(line.strip()) / _VCVARS_REL
        if line.strip() and candidate.is_file():
            return candidate
    return None


def _vcvars_from_disk_scan() -> Path | None:
    """Return the first vcvars64.bat under the Program Files VS roots, newest year first."""
    roots = [Path(os.environ[var]) / "Microsoft Visual Studio"
             for var in ("ProgramFiles", "ProgramFiles(x86)") if os.environ.get(var)]
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


def find_vcvars() -> Path | None:
    """Return the vcvars64.bat of an installed Visual Studio, or None off Windows."""
    if sys.platform != "win32":
        return None
    return _vcvars_from_vswhere() or _vcvars_from_disk_scan()


def _tools_dir() -> Path:
    """Where a provisioning CLI extracts portable tools (cmake, ninja)."""
    return home.tools_dir()


def _toolchains_dir() -> Path:
    """Where a provisioning CLI installs the intel-llvm bundle and AdaptiveCpp."""
    return home.toolchains_dir()


def _discover_installed_toolchains(cfg: ProvisionConfig, values: dict[str, str]) -> None:
    """Record the paths of toolchains installed by the provisioning CLI, if present."""
    base = _toolchains_dir()
    clang = base / "llvm-sycl" / "bin" / ("clang++.exe" if cfg.platform == "windows" else "clang++")
    if clang.is_file():
        values["llvm_root"] = str(base / "llvm-sycl")
    for name in ("acpp.bat", "acpp"):
        acpp = base / "adaptivecpp" / "bin" / name
        if acpp.is_file():
            values["acpp_exe"] = str(acpp)
            break


def toolchain_status(cfg: ProvisionConfig, gpu: bool) -> list[tuple[str, bool, str]]:
    """Return one ``(name, present, detail)`` row per SYCL toolchain (and CUDA if *gpu*)."""
    win = cfg.platform == "windows"
    base = _toolchains_dir()

    clang = base / "llvm-sycl" / "bin" / ("clang++.exe" if win else "clang++")
    intel_ok = clang.is_file() and binary_works(str(clang))

    acpp_path = ""
    for name in ("acpp.bat", "acpp"):
        cand = base / "adaptivecpp" / "bin" / name
        if cand.is_file():
            acpp_path = str(cand)
            break
    acpp_ok = bool(acpp_path) and binary_works(acpp_path)

    # oneAPI installs system-wide (off the deps tree). Trust the same probe
    # the active-compiler row uses so a glob-discovered icx-cl/icpx counts.
    active, _ = find_sycl_compiler(cfg)
    oneapi_bin = (_first_glob(_ICX_GLOBS) or shutil.which("icx-cl")
                  or shutil.which("icpx") or shutil.which("icx")
                  or (_first_glob(_ICX_GLOBS_LINUX) if not win else ""))
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
        nvcc_bin = shutil.which("nvcc") or (_first_glob(_NVCC_GLOBS_LINUX) if not win else "")
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
    reader = _windows_display_adapters if sys.platform == "win32" else _linux_display_adapters
    return classify_display_adapters(reader())


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


def _linux_display_adapters() -> str:
    """Return the lower-case display-controller lines ``lspci`` reports, or ''."""
    try:
        out = subprocess.run(["lspci"], capture_output=True, text=True,
                             timeout=10).stdout.lower()
    except Exception:
        return ""
    return "\n".join(
        ln for ln in out.splitlines()
        if "vga compatible controller" in ln or "3d controller" in ln
        or "display controller" in ln
    )


def _windows_display_adapters() -> str:
    """Return the lower-case names of the video controllers Windows reports, or ''."""
    cmd = ["powershell", "-NoProfile", "-NonInteractive", "-Command",
           "Get-CimInstance Win32_VideoController | ForEach-Object { $_.Name }"]
    try:
        return subprocess.run(cmd, capture_output=True, text=True,
                              timeout=30).stdout.lower()
    except Exception:
        return ""


def binary_works(cmd: str) -> bool:
    """Return True only if *cmd* is on PATH (or an absolute path) and runs cleanly.

    Tries --version first; falls back to -version for tools that use that flag.
    A missing binary, a crash, or a non-zero exit all return False.
    """
    try:
        if subprocess.run([cmd, "--version"], capture_output=True, timeout=15).returncode == 0:
            return True
        return subprocess.run([cmd, "-version"], capture_output=True, timeout=15).returncode == 0
    except Exception:
        return False


def find_sycl_compiler(cfg: ProvisionConfig) -> tuple[str | None, str]:
    """Return (compiler, location) for the active SYCL toolchain, or (None, '').

    Existence of the binary is not enough — a partial install can leave the exe
    on disk with missing DLLs. The binary is verified by running --version.
    """
    if cfg.platform == "windows":
        icx = cfg.expand(cfg.icx_compiler) if cfg.icx_compiler else ""
        if icx and Path(icx).is_file() and binary_works(icx):
            return ("icx-cl", icx)
        hit = _first_glob(_ICX_GLOBS) or shutil.which("icx-cl") or shutil.which("icx") or ""
        if hit and binary_works(hit):
            return ("icx-cl", hit)
        return (None, "")
    # Linux: prefer oneAPI icpx, then intel/llvm clang++.
    for cc in ("icpx", "clang++"):
        path = shutil.which(cc)
        if path and binary_works(path):
            return (cc, path)
    return (None, "")


def find_configured_toolchain(cfg: ProvisionConfig) -> tuple[str | None, str]:
    """Return (label, path) for a SYCL compiler installed by the provisioning CLI, or (None, '')."""
    win = cfg.platform == "windows"
    base = _toolchains_dir()

    bundle = ""
    if cfg.llvm_root:
        cand = Path(cfg.expand(cfg.llvm_root)) / "bin" / ("clang++.exe" if win else "clang++")
        if cand.is_file():
            bundle = str(cand)
    if not bundle:
        cand = base / "llvm-sycl" / "bin" / ("clang++.exe" if win else "clang++")
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
    if cfg.platform == "windows":
        return _resolve_windows(cfg)
    return _resolve_linux(cfg)


def _resolve_windows(cfg: ProvisionConfig) -> dict[str, str]:
    """Probe Windows-specific tool paths for :func:`resolve_local_config`."""
    values: dict[str, str] = {}

    vcvars = cfg.expand(cfg.vs_vcvars) if cfg.vs_vcvars else ""
    if not (vcvars and Path(vcvars).is_file()):
        vcvars = _first_glob(_VS_VCVARS_GLOBS) or str(find_vcvars() or "")
    if vcvars:
        values["vs_vcvars"] = vcvars

    oneapi = cfg.expand(cfg.oneapi_root) if cfg.oneapi_root else ""
    if not (oneapi and Path(oneapi).is_dir()):
        oneapi = _first_existing(_ONEAPI_ROOTS)
    if oneapi:
        values["oneapi_root"] = oneapi

    icx = _first_glob(_ICX_GLOBS) or shutil.which("icx-cl") or shutil.which("icx") or ""
    if icx:
        values["icx_compiler"] = icx

    # clang++ runs GNU-like, not clang-cl, so vcvars is never sourced for rc.exe.
    rc = shutil.which("rc") or _first_glob(_RC_GLOBS)
    if rc:
        values["rc_exe"] = rc

    portable_bin = _tools_dir() / "cmake" / "bin"
    ninja = shutil.which("ninja") or _first_existing([str(_tools_dir() / "ninja.exe")])
    if ninja:
        values["ninja_exe"] = ninja

    # cmake/ctest may be off PATH in a non-interactive shell, so known install locations are checked too.
    _cmake_pf = [str(portable_bin / "cmake.exe"),
                 r"C:/Program Files/CMake/bin/cmake.exe",
                 r"C:/Program Files (x86)/CMake/bin/cmake.exe"]
    _ctest_pf = [str(portable_bin / "ctest.exe"),
                 r"C:/Program Files/CMake/bin/ctest.exe",
                 r"C:/Program Files (x86)/CMake/bin/ctest.exe"]
    cmake = shutil.which("cmake") or _first_existing(_cmake_pf)
    if cmake:
        values["cmake_exe"] = cmake
    ctest = shutil.which("ctest") or _first_existing(_ctest_pf)
    if ctest:
        values["ctest_exe"] = ctest

    pkgconf = shutil.which("pkg-config") or shutil.which("pkgconf")
    vcpkg_root = cfg.expand(cfg.vcpkg_root) if cfg.vcpkg_root else ""
    # Ignore a configured path that points inside a conda/venv tree.
    if vcpkg_root and (".conda" in vcpkg_root or "envs" in vcpkg_root):
        vcpkg_root = ""
    if not (vcpkg_root and Path(vcpkg_root).is_dir()):
        # Default to the dependency root's vcpkg tree when none is configured.
        vcpkg_root = str(home.root() / "vcpkg")
    if vcpkg_root:
        values["vcpkg_root"] = vcpkg_root
        # pkgconf shipped by vcpkg is the one CMakeLists expects.
        vcpkg_pkgconf = Path(vcpkg_root) / "installed" / (cfg.vcpkg_triplet or "x64-windows") / "tools" / "pkgconf" / "pkgconf.exe"
        if vcpkg_pkgconf.is_file():
            pkgconf = str(vcpkg_pkgconf)
    if pkgconf:
        values["pkgconf_exe"] = pkgconf

    doxy = shutil.which("doxygen") or _first_existing([
        str(_tools_dir() / "doxygen" / "doxygen.exe"),
        r"C:/Program Files/doxygen/bin/doxygen.exe",
        r"C:/Program Files (x86)/doxygen/bin/doxygen.exe",
    ])
    if doxy:
        values["doxygen_exe"] = doxy

    _discover_installed_toolchains(cfg, values)
    return values


def _resolve_linux(cfg: ProvisionConfig) -> dict[str, str]:
    """Probe Linux-specific tool paths for :func:`resolve_local_config`."""
    values: dict[str, str] = {}
    compiler, path = find_sycl_compiler(cfg)
    if compiler == "clang++":
        values["cxx"] = "clang++"
        values["cc"] = "clang"
    oneapi = cfg.expand(cfg.oneapi_root) if cfg.oneapi_root else ""
    if oneapi and Path(oneapi, "setvars.sh").is_file():
        values["oneapi_root"] = oneapi
    del path
    _discover_installed_toolchains(cfg, values)
    return values
