# test_layering.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Keeps the sub-package's layers pointing downward and Typer out of module scope."""

from __future__ import annotations

import ast
from pathlib import Path

import sushicore.docs_bundle as docs_bundle

K_ROOT = Path(docs_bundle.__file__).parent
K_LAYER = {
    "errors": 0, "markdown_scan": 0,
    "page_text": 1, "publish_list": 1, "api_reference": 1, "bundle_archive": 1,
    "source_revision": 1,
    "page_order": 2, "page_set": 3, "bundle_manifest": 4, "producer": 5,
    "commands": 6, "__main__": 6,
}
K_COMMAND_FRAMEWORKS = frozenset({"typer", "click"})


def _module_imports(path: Path) -> tuple[set[str], set[str]]:
    """Returns the sibling modules a file imports and the top-level packages it imports."""
    siblings: set[str] = set()
    packages: set[str] = set()
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.ImportFrom) and node.level == 1 and node.module:
            siblings.add(node.module.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            packages.add(node.module.split(".")[0])
        elif isinstance(node, ast.Import):
            packages.update(alias.name.split(".")[0] for alias in node.names)
    return siblings, packages


def test_every_module_has_a_layer():
    """Fails when a file is added without a row in the layer table."""
    modules = {path.stem for path in K_ROOT.glob("*.py")} - {"__init__"}
    assert modules == set(K_LAYER)


def test_no_module_imports_a_higher_or_equal_layer():
    """A module imports only siblings in a lower layer."""
    for name, layer in K_LAYER.items():
        siblings, _ = _module_imports(K_ROOT / f"{name}.py")
        for sibling in siblings:
            assert K_LAYER[sibling] < layer, f"{name} imports {sibling}"


def test_no_module_imports_a_command_framework_at_module_level():
    """Imports no command framework at module level; Typer loads inside the function."""
    for path in K_ROOT.glob("*.py"):
        _, packages = _module_imports(path)
        assert not packages & K_COMMAND_FRAMEWORKS, path.name
