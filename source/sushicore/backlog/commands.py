# commands.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The `backlog` command group, registered on a CLI from where its repository is.

The behaviour of each command is in `docs/reference/BACKLOG.md`.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional

from .check import check_backlog, late_entries
from .editor import BacklogEditor
from .importer import BacklogImporter, BacklogRenumberer
from .model import K_PRIORITIES, IssueEntry, WorkEntry
from .order import age, decisions, is_late, next_work
from .store import AnyEntry, BacklogStore, Located

if TYPE_CHECKING:
    import typer

K_HELP = "Read and change the backlog: remaining work and known issues, in docs/backlog/."
K_EXIT_FINDINGS = 1


def register_backlog_commands(
    app: "typer.Typer",
    *,
    program: str,
    panel: str,
    project_root: Callable[[], Path],
    report: Callable[[str], None] = print,
    group_cls: type | None = None,
) -> None:
    """Adds the `backlog` group to *app*.

    Args:
        app: The application to add the group to.
        program: The command the user types, for the examples.
        panel: The help panel the group is listed under.
        project_root: Returns the repository root; called when a command runs.
        report: Prints one line of the result the way the CLI prints.
        group_cls: The Click group class the CLI draws its help with.
    """
    import typer

    def typer_app(help_text: str) -> typer.Typer:
        """Returns a group with the CLI's help class."""
        options: dict = {"help": help_text, "no_args_is_help": True, "rich_markup_mode": "rich"}
        if group_cls is not None:
            options["cls"] = group_cls
        return typer.Typer(**options)

    backlog_app = typer_app(K_HELP)
    add_app = typer_app("Add a work entry or a known issue.")
    area_app = typer_app("List or add the areas of the backlog.")

    def store() -> BacklogStore:
        """Returns the store of the repository the CLI runs in."""
        return BacklogStore(project_root())

    def emit(payload: object, lines: list[str], as_json: bool) -> None:
        """Prints the result as JSON or as lines."""
        if as_json:
            report(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            for line in lines:
                report(line)

    json_option = typer.Option(False, "--json", help="Print JSON, for an agent.")

    @backlog_app.command("list", epilog=f"{program} backlog list --priority P0..P1\n{program} backlog list --late --json")
    def list_entries(
        area: Optional[str] = typer.Option(None, "--area", help="Only this area."),
        state: Optional[str] = typer.Option(None, "--state", help="Only this state."),
        priority: Optional[str] = typer.Option(None, "--priority", help="A priority, or a range such as P0..P1."),
        kind: Optional[str] = typer.Option(None, "--kind", help="work or issue."),
        late: bool = typer.Option(False, "--late", help="Only work past its age limit."),
        as_json: bool = json_option,
    ) -> None:
        """List entries, filtered."""
        current = store()
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
        emit([_payload(item, today) for item in found], [_line(item.entry, today) for item in found], as_json)

    @backlog_app.command("show", epilog=f"{program} backlog show RW-12")
    def show(ident: str = typer.Argument(..., help="The ID."), as_json: bool = json_option) -> None:
        """Show one entry, with its detail file when it has one."""
        current = store()
        item = current.find(ident)
        detail_path = current.detail_path(ident)
        detail = detail_path.read_text(encoding="utf-8") if detail_path.is_file() else ""
        payload = {**_payload(item, current.today()), "detail": detail}
        columns = item.entry.COLUMNS
        lines = [f"{name}: {value}" for name, value in zip(columns, item.entry.cells())]
        lines.append(f"Area: {item.area}")
        if detail:
            lines += ["", detail.rstrip("\n")]
        emit(payload, lines, as_json)

    @backlog_app.command("next", epilog=f"{program} backlog next\n{program} backlog next --count 3 --json")
    def next_command(
        count: int = typer.Option(5, "--count", help="How many entries."),
        as_json: bool = json_option,
    ) -> None:
        """Print the work an agent should take, first to last."""
        current = store()
        today = current.today()
        chosen = next_work(current.entries(), current.config().pins, today, count)
        located = {item.entry.ident: item for item in current.located()}
        emit(
            [_payload(located[entry.ident], today) for entry in chosen],
            [_line(entry, today) for entry in chosen] or ["no work is ready"],
            as_json,
        )

    @backlog_app.command("decisions", epilog=f"{program} backlog decisions")
    def decisions_command(as_json: bool = json_option) -> None:
        """List the entries waiting for the owner."""
        current = store()
        today = current.today()
        chosen = decisions(current.entries())
        located = {item.entry.ident: item for item in current.located()}
        emit(
            [_payload(located[entry.ident], today) for entry in chosen],
            [_line(entry, today) for entry in chosen] or ["no decision is waiting"],
            as_json,
        )

    @add_app.command("work", epilog=f"{program} backlog add work --area PHYSICS --priority P1 --title \"Fix the step\" --done-when \"the test passes\"")
    def add_work(
        area: str = typer.Option(..., "--area", help="The area."),
        priority: str = typer.Option(..., "--priority", help="P0, P1, P2 or P3."),
        title: str = typer.Option(..., "--title", help="An imperative sentence, at most 90 characters."),
        done_when: str = typer.Option(..., "--done-when", help="One acceptance criterion, at most 160 characters."),
        source: str = typer.Option("", "--source", help="A path from the root, with an optional §<n>."),
        blocked_by: str = typer.Option("", "--blocked-by", help="IDs, or 'external: <reason>'; makes the entry blocked."),
        decision: bool = typer.Option(False, "--decision", help="The entry waits for the owner's ruling."),
        as_json: bool = json_option,
    ) -> None:
        """Add a work entry and print its ID."""
        entry = BacklogEditor(store()).add_work(
            area=area, priority=priority, title=title, done_when=done_when, source=source,
            blocked_by=blocked_by, state="decision" if decision else None,
        )
        emit({"id": entry.ident}, [entry.ident], as_json)

    @add_app.command("issue", epilog=f"{program} backlog add issue --area BUILD --origin toolchain --symptom \"The link fails\" --workaround none")
    def add_issue(
        area: str = typer.Option(..., "--area", help="The area."),
        origin: str = typer.Option(..., "--origin", help="own, toolchain, dependency or '<repository> KI-<n>'."),
        symptom: str = typer.Option(..., "--symptom", help="The symptom as seen, at most 90 characters."),
        workaround: str = typer.Option(..., "--workaround", help="What a reader does, or 'none'."),
        fix: str = typer.Option("", "--fix", help="RW-<n>, or 'none, <reason>'; required when the origin is own."),
        source: str = typer.Option("", "--source", help="A path from the root, with an optional §<n>."),
        as_json: bool = json_option,
    ) -> None:
        """Add a known issue and print its ID."""
        entry = BacklogEditor(store()).add_issue(
            area=area, origin=origin, symptom=symptom, workaround=workaround, fix=fix, source=source,
        )
        emit({"id": entry.ident}, [entry.ident], as_json)

    @backlog_app.command("promote", epilog=f"{program} backlog promote KI-4 --priority P1 --title \"Fix the link\" --done-when \"the link passes\"")
    def promote(
        ident: str = typer.Argument(..., help="The known issue."),
        priority: str = typer.Option(..., "--priority", help="P0, P1, P2 or P3."),
        title: str = typer.Option(..., "--title", help="An imperative sentence."),
        done_when: str = typer.Option(..., "--done-when", help="One acceptance criterion."),
        as_json: bool = json_option,
    ) -> None:
        """Open a work entry from a known issue and print its ID."""
        entry = BacklogEditor(store()).promote(ident, priority=priority, title=title, done_when=done_when)
        emit({"id": entry.ident}, [entry.ident], as_json)

    @backlog_app.command("set", epilog=f"{program} backlog set RW-12 Pri P0\n{program} backlog set RW-12 State open")
    def set_command(
        ident: str = typer.Argument(..., help="The ID."),
        column: str = typer.Argument(..., help="The column, as the table heads it."),
        value: str = typer.Argument(..., help="The new value; an empty string clears it."),
    ) -> None:
        """Change one column of an entry."""
        entry = BacklogEditor(store()).set_value(ident, column, value)
        report(" | ".join(entry.cells()))

    @backlog_app.command("close", epilog=f"{program} backlog close RW-12 --commit 1a2b3c4")
    def close(
        ident: str = typer.Argument(..., help="The ID."),
        commit: str = typer.Option(..., "--commit", help="The commit that closes it."),
        as_json: bool = json_option,
    ) -> None:
        """Delete an entry and print the changelog line to write."""
        closed = BacklogEditor(store()).close(ident, commit=commit)
        emit({"id": ident, "changelog": closed.changelog_line}, [closed.changelog_line], as_json)

    @backlog_app.command("pin", epilog=f"{program} backlog pin RW-12 --at 1")
    def pin(
        ident: str = typer.Argument(..., help="The work entry."),
        at: Optional[int] = typer.Option(None, "--at", help="Its place in the pins, from 1; last by default."),
    ) -> None:
        """Put a work entry in the owner's pins, which `next` returns first."""
        report(", ".join(BacklogEditor(store()).pin(ident, at)))

    @backlog_app.command("unpin", epilog=f"{program} backlog unpin RW-12")
    def unpin(ident: str = typer.Argument(..., help="The pinned entry.")) -> None:
        """Take an entry out of the pins."""
        report(", ".join(BacklogEditor(store()).unpin(ident)) or "no pins")

    @area_app.command("list", epilog=f"{program} backlog area list")
    def area_list(as_json: bool = json_option) -> None:
        """List the areas."""
        areas = list(store().config().areas)
        emit(areas, areas, as_json)

    @area_app.command("add", epilog=f"{program} backlog area add RENDERING")
    def area_add(name: str = typer.Argument(..., help="The area, upper case words joined by _.")) -> None:
        """Add an area and its empty file."""
        report(", ".join(BacklogEditor(store()).add_area(name)))

    @backlog_app.command("move", epilog=f"{program} backlog move RW-12 RENDERING")
    def move(
        ident: str = typer.Argument(..., help="The ID."),
        area: str = typer.Argument(..., help="The area it moves to."),
    ) -> None:
        """Move an entry to another area."""
        left = BacklogEditor(store()).move(ident, area)
        report(f"{ident}: {left} -> {area}")

    @area_app.command("merge", epilog=f"{program} backlog area merge MATTER MATTER_PRECISION")
    def area_merge(
        into: str = typer.Argument(..., help="The area that stays."),
        source: str = typer.Argument(..., help="The area whose entries move and which is deleted."),
    ) -> None:
        """Move every entry of one area into another and delete the emptied one."""
        count = BacklogEditor(store()).merge_areas(into, source)
        report(f"{count} entries: {source} -> {into}")

    @backlog_app.command("renumber", epilog=f"{program} backlog renumber --target main")
    def renumber(target: str = typer.Option("main", "--target", help="The branch whose entries keep their IDs.")) -> None:
        """Give each entry that shares an ID with another the next free number."""
        result = BacklogRenumberer(store(), target).run()
        lines = [f"{old} -> {new}" for old, new in result.renames]
        for line in lines or ["no ID is shared"]:
            report(line)

    @backlog_app.command("import", epilog=f"{program} backlog import")
    def import_command() -> None:
        """Move REMAINING_WORK.md and KNOWN_ISSUES.md into docs/backlog/, once."""
        result = BacklogImporter(store()).run()
        report(f"{result.work} work entries, {result.issues} known issues, {result.details} detail files")
        report(f"areas: {', '.join(result.areas)}")
        report(f"pins: {', '.join(result.pins) or 'none'}")
        report(f"citations rewritten: {len(result.rewrites)}")
        for path in result.left:
            report(f"still names a retired file, for its author to change: {_shown(path, project_root())}")

    @backlog_app.command("check", epilog=f"{program} backlog check\n{program} backlog check --report")
    def check(report_flag: bool = typer.Option(False, "--report", help="Also print the late work.")) -> None:
        """Check the backlog against every rule; exits 1 on a finding."""
        root = project_root()
        current = BacklogStore(root)
        faults = check_backlog(current, lambda: _open_designs(root))
        for fault in faults:
            report(f"{_shown(fault.path, root)}:{fault.line}: {fault.message}")
        if report_flag and not faults and current.exists():
            today = current.today()
            late = late_entries(current, today)
            report(f"late: {len(late)}")
            for entry in late:
                report(f"  {_line(entry, today)}")
        if faults:
            raise typer.Exit(K_EXIT_FINDINGS)
        report("clean")

    backlog_app.add_typer(add_app, name="add")
    backlog_app.add_typer(area_app, name="area")
    app.add_typer(backlog_app, name="backlog", rich_help_panel=panel)


def _open_designs(root: Path) -> list[Path]:
    """Returns the open design topics of the repository, for the coverage rule."""
    from ..design.store import DesignStore

    return DesignStore(root).open_documents()


def _priority_range(text: str | None) -> tuple[str, ...]:
    """Returns the priorities a value such as `P1` or `P0..P2` names."""
    if not text:
        return ()
    low, _, high = text.partition("..")
    if low not in K_PRIORITIES or (high and high not in K_PRIORITIES):
        return (text,)
    end = K_PRIORITIES.index(high or low)
    return K_PRIORITIES[K_PRIORITIES.index(low): end + 1]


def _payload(item: Located, today: datetime.date) -> dict:
    """Returns an entry as a JSON object: its columns, its area, and for work its age."""
    entry = item.entry
    payload: dict = dict(zip(entry.COLUMNS, entry.cells()))
    payload["Kind"] = "work" if isinstance(entry, WorkEntry) else "issue"
    payload["Area"] = item.area
    payload["Age"] = age(entry, today)
    if isinstance(entry, WorkEntry):
        payload["Late"] = is_late(entry, today)
    return payload


def _line(entry: AnyEntry, today: datetime.date) -> str:
    """Returns one entry as a line of text."""
    if isinstance(entry, IssueEntry):
        return f"{entry.ident} {entry.origin}: {entry.symptom}"
    late = " late" if is_late(entry, today) else ""
    return f"{entry.ident} {entry.priority} {entry.state}{late} {age(entry, today)}d: {entry.title}"


def _shown(path: Path, root: Path) -> str:
    """Returns a path from the root when it is under it."""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)
