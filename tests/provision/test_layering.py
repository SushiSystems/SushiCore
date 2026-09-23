# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License, Version 2.0. See LICENSE.
"""Keeps provision's layers pointing downward and free of hub."""

from __future__ import annotations

import ast
from pathlib import Path

import sushicore.provision as provision

_ROOT = Path(provision.__file__).parent
_LAYER = {
    "_output": 0, "config": 0, "home": 0,
    "system": 1, "probe": 1, "toolchains.stamp": 1, "gpu.compiler_identity": 1,
    "gpu.windows_installer": 1, "fragments": 1, "registry": 1, "lock": 1, "doctor": 1,
    "pipeline": 1, "sinks": 2, "gpu.backend": 2, "gpu.cuda": 2, "gpu.rocm": 2,
    "gpu.level_zero": 2, "gpu.registry": 2, "gpu.provisioning": 2, "gpu.adapter_builder": 2,
    "gpu": 2, "checks": 2, "packages": 3, "toolchains": 4, "toolchains.intel_llvm": 4,
    "toolchains.adaptivecpp": 4, "toolchains.oneapi": 4, "toolchains._process": 1,
    "steps": 5, "commands": 6,
}


def _module_name(path: Path) -> str:
    rel = path.relative_to(_ROOT).with_suffix("")
    parts = [p for p in rel.parts if p != "__init__"]
    if parts and parts[0] == "packages":
        return "packages"
    return ".".join(parts)


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            names.add(("." * node.level) + node.module)
        elif isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
    return names


def test_no_module_imports_hub():
    for path in _ROOT.rglob("*.py"):
        assert not any("sushihub" in n for n in _imports(path)), path


def test_every_module_has_a_layer():
    for path in _ROOT.rglob("*.py"):
        name = _module_name(path)
        if name:
            assert name in _LAYER, name


def _resolve(path: Path, imported: str) -> str | None:
    """Return the provision module a relative import names, or None for other imports."""
    level = len(imported) - len(imported.lstrip("."))
    if level == 0:
        prefix = "sushicore.provision."
        return imported[len(prefix):] if imported.startswith(prefix) else None
    base = list(path.relative_to(_ROOT).with_suffix("").parts[:-1])
    base = base[:len(base) - (level - 1)] if level > 1 else base
    target = [*base, *[p for p in imported.lstrip(".").split(".") if p]]
    if target and target[0] == "packages":
        return "packages"
    name = ".".join(target)
    return name if name in _LAYER else None


def test_imports_point_down_or_sideways():
    for path in _ROOT.rglob("*.py"):
        own = _module_name(path)
        if not own:
            continue
        for imported in _imports(path):
            target = _resolve(path, imported)
            if target and target != own:
                assert _LAYER[target] <= _LAYER[own], f"{own} imports {target}"
