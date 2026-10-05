# describe.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026 Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The command catalogue a Sushi CLI prints for ``--describe``.

A serialisation of the Typer application's own Click command objects, so a new subcommand
reaches a caller without a second declaration of it anywhere. Nothing here names a command.
The shape is the one SushiHub's ``contract/describe.schema.json`` fixes.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING, Sequence

from rich.errors import MarkupError
from rich.text import Text

if TYPE_CHECKING:
    import click
    import typer

K_CONTRACT_VERSION = "1"
K_UNKNOWN_VERSION = "0"
K_CLICK_PARAMETERS = frozenset({"help"})
K_TYPE_NAMES = {"choice": "choice", "path": "path", "boolean": "boolean",
                "integer": "integer", "float": "number"}


def _plain(text: str) -> str:
    """Returns *text* with its Rich markup tags removed."""
    try:
        return Text.from_markup(text).plain
    except MarkupError:
        return text


def _first_paragraph(help_text: str | None) -> str:
    """Returns the first paragraph of *help_text* as one markup-free line."""
    lines: list[str] = []
    for line in (help_text or "").splitlines():
        if not line.strip():
            break
        lines.append(line.strip())
    return _plain(" ".join(lines))


def _type_name(param_type: "click.ParamType") -> str:
    """Names a parameter type as one of the six names the contract allows, by its own name."""
    return K_TYPE_NAMES.get(str(getattr(param_type, "name", "")).lower(), "string")


def _choices(param_type: "click.ParamType") -> list[str] | None:
    """Returns a choice type's values as strings, or None for every other type."""
    choices = getattr(param_type, "choices", None)
    return None if choices is None else [str(choice) for choice in choices]


def _default(param: "click.Parameter"):
    """Returns a parameter's default as JSON data, with an unset default as None."""
    value = param.default
    if value is Ellipsis:
        return None
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value]
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    return str(value)


def _param(param: "click.Parameter") -> dict:
    """Describes one argument or option."""
    argument = getattr(param, "param_type_name", "") == "argument"
    return {
        "name": param.name,
        "kind": "argument" if argument else "option",
        "type": _type_name(param.type),
        "multiple": bool(param.multiple or param.nargs == -1),
        "required": bool(param.required),
        "default": _default(param),
        "choices": _choices(param.type),
        "flags": [] if argument else list(param.opts),
        "help": _plain(getattr(param, "help", "") or ""),
    }


def _command(name: str, command: "click.Command", applies_to: Sequence[str]) -> dict:
    """Describes one command and every parameter a caller can set."""
    return {
        "name": name,
        "help": _first_paragraph(command.help),
        "params": [_param(p) for p in command.params if p.name not in K_CLICK_PARAMETERS],
        "applies_to": list(applies_to),
    }


def _flatten(group: "click.Group", applies_to: Sequence[str], prefix: str = "") -> list[dict]:
    """Describes every visible leaf command under *group*, sorted, with its full name.

    A nested group is not a command a caller can run, so it contributes its children under
    ``"<group> <child>"`` and no entry of its own. A hidden command or group is an old
    spelling and is left out.
    """
    described: list[dict] = []
    for name in sorted(getattr(group, "commands", {})):
        command = group.commands[name]
        if getattr(command, "hidden", False):
            continue
        if hasattr(command, "commands"):
            described.extend(_flatten(command, applies_to, prefix + name + " "))
        else:
            described.append(_command(prefix + name, command, applies_to))
    return described


def installed_version(distribution: str) -> str | None:
    """Returns the installed version of *distribution*, or None when it is not installed."""
    try:
        return version(distribution)
    except PackageNotFoundError:
        return None


def catalogue(app: "typer.Typer", *, distribution: str, applies_to: Sequence[str] = ()) -> dict:
    """Serialises *app*'s visible commands, sorted by name, as the catalogue the contract fixes.

    Args:
        app: The Typer application to describe.
        distribution: The distribution whose installed version the catalogue reports.
        applies_to: What every command's ``applies_to`` holds; SushiHub passes the forms of
            module presence, a module CLI passes nothing.

    Returns:
        A dict matching SushiHub's ``contract/describe.schema.json``.
    """
    import typer.main

    group = typer.main.get_command(app)
    return {
        "program": app.info.name or group.name or "",
        "version": installed_version(distribution) or K_UNKNOWN_VERSION,
        "contract": K_CONTRACT_VERSION,
        "commands": _flatten(group, applies_to),
    }
