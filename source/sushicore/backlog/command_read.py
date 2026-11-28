# command_read.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The `backlog` commands that read the store: list, show, next, here, decisions, flow, stale and check."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Optional

from .admission import entries_on
from .check import check_backlog, late_entries
from .command_context import CommandContext, entry_line, entry_payload, json_option, shown_path
from .flow import K_FLOW_DAYS, measure_flow
from .history import Recorded
from .model import K_PRIORITIES, WorkEntry
from .order import decisions, is_late, next_work
from .store import BacklogStore
from .triage import K_TRIAGE_DAYS, stale_work

if TYPE_CHECKING:
    import typer

K_EXIT_FINDINGS = 1
K_NO_HISTORY = "git cannot read the history of docs/backlog/"


def register_list(group: "typer.Typer", context: CommandContext) -> None:
    """Adds `list`: the entries, filtered by area, state, priority, kind and lateness."""
    import typer

    @group.command(
        "list",
        epilog=f"{context.program} backlog list --priority P0..P1\n{context.program} backlog list --late --json",
    )
    def list_entries(
        area: Optional[str] = typer.Option(None, "--area", help="Only this area."),
        state: Optional[str] = typer.Option(None, "--state", help="Only this state."),
        priority: Optional[str] = typer.Option(None, "--priority", help="A priority, or a range such as P0..P1."),
        kind: Optional[str] = typer.Option(None, "--kind", help="work or issue."),
        late: bool = typer.Option(False, "--late", help="Only work past its age limit."),
        as_json: bool = json_option(),
    ) -> None:
        """List entries, filtered."""
        current = context.store()
        today = current.today()
        allowed = _priority_range(priority)
        found = []
        for item in current.located():
            entry = item.entry
            if area and item.area != area:
                continue
            if kind and (kind == "work") != isinstance(entry, WorkEntry):
                continue
            if isinstance(entry, WorkEntry):
                if state and entry.state != state:
                    continue
                if allowed and entry.priority not in allowed:
                    continue
                if late and not is_late(entry, today):
                    continue
            elif state or allowed or late:
                continue
            found.append(item)
        context.emit_entries(found, "", as_json)


def register_show(group: "typer.Typer", context: CommandContext) -> None:
    """Adds `show`: one entry with its detail file."""
    import typer

    @group.command("show", epilog=f"{context.program} backlog show RW-12")
    def show(ident: str = typer.Argument(..., help="The ID."), as_json: bool = json_option()) -> None:
        """Show one entry, with its detail file when it has one."""
        current = context.store()
        item = current.find(ident)
        detail_path = current.detail_path(ident)
        detail = detail_path.read_text(encoding="utf-8") if detail_path.is_file() else ""
        payload = {**entry_payload(item, current.today()), "detail": detail}
        lines = [f"{name}: {value}" for name, value in zip(item.entry.COLUMNS, item.entry.cells())]
        lines.append(f"Area: {item.area}")
        if detail:
            lines += ["", detail.rstrip("\n")]
        context.emit(payload, lines, as_json)


def register_next(group: "typer.Typer", context: CommandContext) -> None:
    """Adds `next`: the work an agent should take, first to last."""
    import typer

    @group.command(
        "next", epilog=f"{context.program} backlog next\n{context.program} backlog next --count 3 --json",
    )
    def next_command(
        count: int = typer.Option(5, "--count", help="How many entries."),
        as_json: bool = json_option(),
    ) -> None:
        """Print the work an agent should take, first to last."""
        current = context.store()
        chosen = next_work(current.entries(), current.config().pins, current.today(), count)
        located = {item.entry.ident: item for item in current.located()}
        context.emit_entries([located[entry.ident] for entry in chosen], "no work is ready", as_json)


def register_here(group: "typer.Typer", context: CommandContext) -> None:
    """Adds `here`: the open entries whose Source covers the given paths."""
    import typer

    @group.command(
        "here", epilog=f"{context.program} backlog here source/physics/step.cpp\n"
                       f"{context.program} backlog here source/physics --json",
    )
    def here(
        paths: list[str] = typer.Argument(..., help="Files or folders, from the root or the current folder."),
        as_json: bool = json_option(),
    ) -> None:
        """List the open entries whose Source covers a path, before changing it."""
        root = context.project_root()
        wanted = [_from_root(Path(path), root) for path in paths]
        located = list(context.store().located())
        chosen = {entry.ident for entry in entries_on([item.entry for item in located], wanted)}
        context.emit_entries(
            [item for item in located if item.entry.ident in chosen], "no open entry names these paths",
            as_json)


def register_decisions(group: "typer.Typer", context: CommandContext) -> None:
    """Adds `decisions`: the entries that wait for the owner."""

    @group.command("decisions", epilog=f"{context.program} backlog decisions")
    def decisions_command(as_json: bool = json_option()) -> None:
        """List the entries waiting for the owner."""
        current = context.store()
        today = current.today()
        chosen = decisions(current.entries())
        located = {item.entry.ident: item for item in current.located()}
        context.emit(
            [entry_payload(located[entry.ident], today) for entry in chosen],
            [entry_line(entry, today) for entry in chosen] or ["no decision is waiting"],
            as_json,
        )


def register_flow(group: "typer.Typer", context: CommandContext) -> None:
    """Adds `flow`: what opened and closed in a window, and the open work changed and left open."""
    import typer

    @group.command(
        "flow", epilog=f"{context.program} backlog flow\n{context.program} backlog flow --days 30 --json",
    )
    def flow(
        days: int = typer.Option(K_FLOW_DAYS, "--days", help="The length of the window, in days."),
        as_json: bool = json_option(),
    ) -> None:
        """Measure the flow of remaining work, read from git."""
        recorded = _history_or_exit(context)
        measured = measure_flow(recorded, context.store().today(), days)
        context.emit(measured.payload(), measured.lines(), as_json)


def register_stale(group: "typer.Typer", context: CommandContext) -> None:
    """Adds `stale`: the work past the triage age, for the owner's triage."""
    import typer

    @group.command(
        "stale", epilog=f"{context.program} backlog stale\n{context.program} backlog stale --days 30 --json",
    )
    def stale(
        days: int = typer.Option(K_TRIAGE_DAYS, "--days", help="The triage age, in days."),
        as_json: bool = json_option(),
    ) -> None:
        """List the work opened more than the triage age ago, with the commits that changed its Source."""
        recorded = _history_or_exit(context)
        current = context.store()
        today = current.today()
        found = stale_work(current.entries(), recorded.changes, today, days)
        located = {item.entry.ident: item for item in current.located()}
        context.emit(
            [{**entry_payload(located[item.entry.ident], today), "Touches": item.touches} for item in found],
            [f"{entry_line(item.entry, today)} ({item.touches} later commits to its Source)" for item in found]
            or [f"no work is older than {days} days"],
            as_json,
        )


def register_check(group: "typer.Typer", context: CommandContext) -> None:
    """Adds `check`: every rule of the backlog, with an exit code of 1 on a finding."""
    import typer

    @group.command(
        "check", epilog=f"{context.program} backlog check\n{context.program} backlog check --report",
    )
    def check(report_flag: bool = typer.Option(False, "--report", help="Also print the late work.")) -> None:
        """Check the backlog against every rule; exits 1 on a finding."""
        root = context.project_root()
        current = BacklogStore(root)
        faults = check_backlog(current)
        for fault in faults:
            context.report(f"{shown_path(fault.path, root)}:{fault.line}: {fault.message}")
        if report_flag and not faults and current.exists():
            today = current.today()
            late = late_entries(current, today)
            context.report(f"late: {len(late)}")
            for entry in late:
                context.report(f"  {entry_line(entry, today)}")
        if faults:
            raise typer.Exit(K_EXIT_FINDINGS)
        context.report("clean")


def _history_or_exit(context: CommandContext) -> Recorded:
    """Returns what git recorded of the backlog, or prints why not and exits with code 1."""
    import typer

    recorded = context.history()
    if recorded is None:
        context.report(K_NO_HISTORY)
        raise typer.Exit(K_EXIT_FINDINGS)
    return recorded


def _from_root(path: Path, root: Path) -> str:
    """Returns a path as the repository root names it, when it lies under the root."""
    absolute = path if path.is_absolute() else Path.cwd() / path
    try:
        return absolute.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _priority_range(text: str | None) -> tuple[str, ...]:
    """Returns the priorities a value such as `P1` or `P0..P2` names."""
    if not text:
        return ()
    low, _, high = text.partition("..")
    if low not in K_PRIORITIES or (high and high not in K_PRIORITIES):
        return (text,)
    end = K_PRIORITIES.index(high or low)
    return K_PRIORITIES[K_PRIORITIES.index(low): end + 1]

