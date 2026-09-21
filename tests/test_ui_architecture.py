"""Every ui/ file is one component, shaped like its siblings, importing only what it may."""

import ast
import dataclasses
import importlib
import inspect
import sys
from pathlib import Path

import pytest

K_UI = Path(__file__).resolve().parent.parent / "sushicore" / "ui"
K_PACKAGE = ("sushicore", "ui")
K_ALLOWED_INTERNAL = {"sushicore.theme", "sushicore.brand", "sushicore.ui.component"}
K_ALLOWED_EXTERNAL = {"rich"}
K_FILES = sorted(p for p in K_UI.glob("*.py") if p.name not in {"__init__.py", "component.py"})


def _pascal(stem: str) -> str:
    """Return a file stem in Pascal case."""
    return "".join(word.capitalize() for word in stem.split("_"))


def _absolute_name(node: ast.ImportFrom) -> str:
    """Return the module name a ``from`` import in a ui/ file names, relative ones resolved."""
    if not node.level:
        return node.module or ""
    depth = len(K_PACKAGE) - (node.level - 1)
    base = K_PACKAGE[:depth] if depth > 0 else ()
    return ".".join([*base, *([node.module] if node.module else [])])


def _imported_modules(tree: ast.AST) -> list[str]:
    """Return every module name the tree imports."""
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names.append(_absolute_name(node))
    return names


def test_the_protocol_file_declares_render():
    module = importlib.import_module("sushicore.ui.component")
    assert callable(module.Component.render)


@pytest.mark.parametrize("path", K_FILES, ids=lambda p: p.name)
def test_file_defines_one_public_class_named_after_the_file(path):
    module = importlib.import_module(f"sushicore.ui.{path.stem}")
    public = [
        name
        for name, value in vars(module).items()
        if isinstance(value, type)
        and value.__module__ == module.__name__
        and not name.startswith("_")
    ]
    assert public == [_pascal(path.stem)]


@pytest.mark.parametrize("path", K_FILES, ids=lambda p: p.name)
def test_component_is_a_frozen_dataclass_with_render(path):
    module = importlib.import_module(f"sushicore.ui.{path.stem}")
    component = getattr(module, _pascal(path.stem))
    assert dataclasses.is_dataclass(component)
    assert component.__dataclass_params__.frozen
    assert callable(component.render)


@pytest.mark.parametrize("path", K_FILES, ids=lambda p: p.name)
def test_render_takes_exactly_self_and_theme(path):
    module = importlib.import_module(f"sushicore.ui.{path.stem}")
    component = getattr(module, _pascal(path.stem))
    assert list(inspect.signature(component.render).parameters) == ["self", "theme"]


@pytest.mark.parametrize("path", K_FILES, ids=lambda p: p.name)
def test_component_uses_slots(path):
    module = importlib.import_module(f"sushicore.ui.{path.stem}")
    assert hasattr(getattr(module, _pascal(path.stem)), "__slots__")


@pytest.mark.parametrize("path", K_FILES, ids=lambda p: p.name)
def test_component_is_marked_final(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    (definition,) = [
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == _pascal(path.stem)
    ]
    names = {ast.unparse(decorator).split(".")[-1] for decorator in definition.decorator_list}
    assert "final" in names


@pytest.mark.parametrize("path", K_FILES, ids=lambda p: p.name)
def test_file_imports_only_what_a_component_may(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for name in _imported_modules(tree):
        root = name.split(".")[0]
        allowed = (
            root in sys.stdlib_module_names
            or root in K_ALLOWED_EXTERNAL
            or name in K_ALLOWED_INTERNAL
        )
        assert allowed, f"{path.name} imports {name}"
