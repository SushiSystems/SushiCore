# gpu_vendor.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Names the discrete-GPU vendor of this machine from its tools and its display adapters."""

from __future__ import annotations

import shutil

from sushicore.provision.host import current_host
from sushicore.quiet_runner import quiet_runner

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
    return classify_display_adapters(current_host().display_adapters(quiet_runner()))
