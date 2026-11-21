# command_write.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The `backlog` commands that change the store: add, promote, set, close, pin, move, the areas and renumber."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from .command_context import CommandContext, json_option
from .editor import BacklogEditor
from .renumber import BacklogRenumberer

if TYPE_CHECKING:
    import typer


def register_add_work(group: "typer.Typer", context: CommandContext) -> None:
    """Adds `add work`: a work entry, printing the ID it took."""
    import typer

    @group.command(
        "work",
        epilog=f"{context.program} backlog add work --area PHYSICS --priority P1 --title \"Fix the step\" "
               "--done-when \"the test passes\"",
    )
    def add_work(
        area: str = typer.Option(..., "--area", help="The area."),
        priority: str = typer.Option(..., "--priority", help="P0, P1, P2 or P3."),
        title: str = typer.Option(..., "--title", help="An imperative sentence, at most 90 characters."),
        done_when: str = typer.Option(..., "--done-when", help="One acceptance criterion, at most 160 characters."),
        source: str = typer.Option("", "--source", help="A path from the root, with an optional §<n>."),
        blocked_by: str = typer.Option("", "--blocked-by", help="IDs, or 'external: <reason>'; makes the entry blocked."),
        decision: bool = typer.Option(False, "--decision", help="The entry waits for the owner's ruling."),
        as_json: bool = json_option(),
    ) -> None:
        """Add a work entry and print its ID."""
        entry = BacklogEditor(context.store()).add_work(
            area=area, priority=priority, title=title, done_when=done_when, source=source,
            blocked_by=blocked_by, state="decision" if decision else None,
        )
        context.emit({"id": entry.ident}, [entry.ident], as_json)


def register_add_issue(group: "typer.Typer", context: CommandContext) -> None:
    """Adds `add issue`: a known issue, printing the ID it took."""
    import typer

    @group.command(
        "issue",
        epilog=f"{context.program} backlog add issue --area BUILD --origin toolchain --symptom \"The link fails\" "
               "--workaround none",
    )
    def add_issue(
        area: str = typer.Option(..., "--area", help="The area."),
        origin: str = typer.Option(..., "--origin", help="own, toolchain, dependency or '<repository> KI-<n>'."),
        symptom: str = typer.Option(..., "--symptom", help="The symptom as seen, at most 90 characters."),
        workaround: str = typer.Option(..., "--workaround", help="What a reader does, or 'none'."),
        fix: str = typer.Option("", "--fix", help="RW-<n>, or 'none, <reason>'; required when the origin is own."),
        source: str = typer.Option("", "--source", help="A path from the root, with an optional §<n>."),
        as_json: bool = json_option(),
    ) -> None:
        """Add a known issue and print its ID."""
        entry = BacklogEditor(context.store()).add_issue(
            area=area, origin=origin, symptom=symptom, workaround=workaround, fix=fix, source=source,
        )
        context.emit({"id": entry.ident}, [entry.ident], as_json)


def register_promote(group: "typer.Typer", context: CommandContext) -> None:
    """Adds `promote`: a work entry opened from a known issue."""
    import typer

    @group.command(
        "promote",
        epilog=f"{context.program} backlog promote KI-4 --priority P1 --title \"Fix the link\" "
               "--done-when \"the link passes\"",
    )
    def promote(
        ident: str = typer.Argument(..., help="The known issue."),
        priority: str = typer.Option(..., "--priority", help="P0, P1, P2 or P3."),
        title: str = typer.Option(..., "--title", help="An imperative sentence."),
        done_when: str = typer.Option(..., "--done-when", help="One acceptance criterion."),
        as_json: bool = json_option(),
    ) -> None:
        """Open a work entry from a known issue and print its ID."""
        entry = BacklogEditor(context.store()).promote(ident, priority=priority, title=title, done_when=done_when)
        context.emit({"id": entry.ident}, [entry.ident], as_json)


def register_set(group: "typer.Typer", context: CommandContext) -> None:
    """Adds `set`: one column of an entry."""
    import typer

    @group.command(
        "set", epilog=f"{context.program} backlog set RW-12 Pri P0\n{context.program} backlog set RW-12 State open",
    )
    def set_command(
        ident: str = typer.Argument(..., help="The ID."),
        column: str = typer.Argument(..., help="The column, as the table heads it."),
        value: str = typer.Argument(..., help="The new value; an empty string clears it."),
    ) -> None:
        """Change one column of an entry."""
        entry = BacklogEditor(context.store()).set_value(ident, column, value)
        context.report(" | ".join(entry.cells()))


def register_close(group: "typer.Typer", context: CommandContext) -> None:
    """Adds `close`: deletes an entry and prints the changelog line to write."""
    import typer

    @group.command(
        "close",
        epilog=f"{context.program} backlog close RW-12\n{context.program} backlog close RW-12 --commit 1a2b3c4",
    )
    def close(
        ident: str = typer.Argument(..., help="The ID."),
        commit: Optional[str] = typer.Option(
            None, "--commit",
            help="The commit that did the work, when it exists; leave it out to close in that commit.",
        ),
        as_json: bool = json_option(),
    ) -> None:
        """Delete an entry and print the changelog line to write."""
        closed = BacklogEditor(context.store()).close(ident, commit=commit)
        context.emit({"id": ident, "changelog": closed.changelog_line}, [closed.changelog_line], as_json)


def register_pin(group: "typer.Typer", context: CommandContext) -> None:
    """Adds `pin`: a work entry in the owner's pins."""
    import typer

    @group.command("pin", epilog=f"{context.program} backlog pin RW-12 --at 1")
    def pin(
        ident: str = typer.Argument(..., help="The work entry."),
        at: Optional[int] = typer.Option(None, "--at", help="Its place in the pins, from 1; last by default."),
    ) -> None:
        """Put a work entry in the owner's pins, which `next` returns first."""
        context.report(", ".join(BacklogEditor(context.store()).pin(ident, at)))


def register_unpin(group: "typer.Typer", context: CommandContext) -> None:
    """Adds `unpin`: an entry out of the pins."""
    import typer

    @group.command("unpin", epilog=f"{context.program} backlog unpin RW-12")
    def unpin(ident: str = typer.Argument(..., help="The pinned entry.")) -> None:
        """Take an entry out of the pins."""
        context.report(", ".join(BacklogEditor(context.store()).unpin(ident)) or "no pins")


def register_move(group: "typer.Typer", context: CommandContext) -> None:
    """Adds `move`: an entry to another area."""
    import typer

    @group.command("move", epilog=f"{context.program} backlog move RW-12 RENDERING")
    def move(
        ident: str = typer.Argument(..., help="The ID."),
        area: str = typer.Argument(..., help="The area it moves to."),
    ) -> None:
        """Move an entry to another area."""
        left = BacklogEditor(context.store()).move(ident, area)
        context.report(f"{ident}: {left} -> {area}")


def register_area_list(group: "typer.Typer", context: CommandContext) -> None:
    """Adds `area list`: the areas of the backlog."""

    @group.command("list", epilog=f"{context.program} backlog area list")
    def area_list(as_json: bool = json_option()) -> None:
        """List the areas."""
        areas = list(context.store().config().areas)
        context.emit(areas, areas, as_json)


def register_area_add(group: "typer.Typer", context: CommandContext) -> None:
    """Adds `area add`: an area and its empty file."""
    import typer

    @group.command("add", epilog=f"{context.program} backlog area add RENDERING")
    def area_add(name: str = typer.Argument(..., help="The area, upper case words joined by _.")) -> None:
        """Add an area and its empty file."""
        context.report(", ".join(BacklogEditor(context.store()).add_area(name)))


def register_area_merge(group: "typer.Typer", context: CommandContext) -> None:
    """Adds `area merge`: the entries of one area into another, and the emptied area deleted."""
    import typer

    @group.command("merge", epilog=f"{context.program} backlog area merge MATTER MATTER_PRECISION")
    def area_merge(
        into: str = typer.Argument(..., help="The area that stays."),
        source: str = typer.Argument(..., help="The area whose entries move and which is deleted."),
    ) -> None:
        """Move every entry of one area into another and delete the emptied one."""
        count = BacklogEditor(context.store()).merge_areas(into, source)
        context.report(f"{count} entries: {source} -> {into}")


def register_renumber(group: "typer.Typer", context: CommandContext) -> None:
    """Adds `renumber`: the merge of two branches of the backlog."""
    import typer

    @group.command("renumber", epilog=f"{context.program} backlog renumber --target main")
    def renumber(
        target: str = typer.Option("main", "--target", help="The branch whose entries keep their IDs."),
    ) -> None:
        """Give each entry that shares an ID with another the next free number."""
        result = BacklogRenumberer(context.store(), target).run()
        lines = [f"{old} -> {new}" for old, new in result.renames]
        for line in lines or ["no ID is shared"]:
            context.report(line)
        context.report("ids.toml and README.md are rewritten from both sides of any conflict")
