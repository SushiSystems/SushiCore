"""Reads a Click or Typer command into a HelpModel.

The model's text is Rich markup; text from a command that does not write markup is escaped.
"""

from __future__ import annotations

import inspect
from typing import Any

from rich.markup import escape

from .model import HelpModel, HelpSection

K_DEFAULT_GROUP = "Commands"
K_SHORT_HELP_LIMIT = 120
K_RICH_MODE = "rich"


def build_model(command: Any, ctx: Any) -> HelpModel:
    """Return the help model of ``command`` as seen from ``ctx``."""
    return HelpModel(
        name=ctx.command_path,
        description=_markup(_description(command), command),
        usage=" ".join([ctx.command_path, *command.collect_usage_pieces(ctx)]),
        is_root=ctx.parent is None,
        commands=_command_sections(command, ctx),
        arguments=_param_entries(command, ctx, "argument"),
        options=_param_entries(command, ctx, "option"),
        examples=_examples(command),
    )


def _description(command: Any) -> str:
    """Return the help text up to a form feed, each paragraph on one line."""
    text = _text(getattr(command, "help", None)).split("\f")[0]
    paragraphs = [" ".join(paragraph.split()) for paragraph in text.split("\n\n")]
    return "\n\n".join(paragraph for paragraph in paragraphs if paragraph)


def _command_sections(command: Any, ctx: Any) -> tuple[HelpSection, ...]:
    """Return the visible sub-commands grouped by panel, in order of first appearance."""
    list_commands = getattr(command, "list_commands", None)
    if list_commands is None:
        return ()
    grouped: dict[str, list[tuple[str, str]]] = {}
    for name in list_commands(ctx):
        sub = command.get_command(ctx, name)
        if sub is None or getattr(sub, "hidden", False):
            continue
        heading = _text(getattr(sub, "rich_help_panel", None)) or K_DEFAULT_GROUP
        short_help = _markup(sub.get_short_help_str(K_SHORT_HELP_LIMIT), sub)
        grouped.setdefault(heading, []).append((name, short_help))
    return tuple(HelpSection(heading, tuple(entries)) for heading, entries in grouped.items())


def _param_entries(command: Any, ctx: Any, kind: str) -> tuple[tuple[str, str], ...]:
    """Return the visible parameters of one kind as term and text pairs."""
    entries = []
    for param in command.get_params(ctx):
        if param.param_type_name != kind or getattr(param, "hidden", False):
            continue
        entry = _entry(param, ctx)
        if entry is not None:
            entries.append((entry[0], _markup(entry[1], command)))
    return tuple(entries)


def _entry(param: Any, ctx: Any) -> tuple[str, str] | None:
    """Return the parameter's help record, or its metavar when it has none."""
    get_record = getattr(param, "get_help_record", None)
    record = get_record(ctx) if get_record is not None else None
    if record is not None:
        return record[0], record[1] or ""
    if param.param_type_name == "argument":
        return _metavar(param, ctx), _text(getattr(param, "help", None))
    return None


def _metavar(param: Any, ctx: Any) -> str:
    """Return the parameter's metavar, passing the context only when it takes one."""
    make_metavar = param.make_metavar
    if inspect.signature(make_metavar).parameters:
        return make_metavar(ctx)
    return make_metavar()


def _examples(command: Any) -> tuple[tuple[str, str], ...]:
    """Return one example per non-empty epilog line, split at the first ``" # "``."""
    entries = []
    for line in _text(getattr(command, "epilog", None)).splitlines():
        line = line.strip()
        if line:
            example, _, note = line.partition(" # ")
            entries.append((example.strip(), note.strip()))
    return tuple(entries)


def _markup(text: str, owner: Any) -> str:
    """Return ``text`` as Rich markup: kept when ``owner`` writes Rich markup, escaped otherwise."""
    mode = getattr(owner, "rich_markup_mode", None)
    # Typer stores its default mode as a wrapper object that carries the mode in ``value``.
    mode = getattr(mode, "value", mode)
    return text if mode == K_RICH_MODE else escape(text)


def _text(value: Any) -> str:
    """Return the value when it is a string, and the empty string for anything else."""
    return value if isinstance(value, str) else ""
