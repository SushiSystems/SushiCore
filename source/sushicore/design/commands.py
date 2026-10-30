# commands.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The `design` command group, registered on a CLI from where its repository is.

The behaviour of each command is in `docs/reference/DESIGN.md`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from ..command_groups import K_DESIGN
from .check import check_design
from .merge import TopicMerger, find_overlap
from .model import K_CLOSED_PHASE_STATES, split_values
from .store import DesignStore

if TYPE_CHECKING:
    import typer

K_HELP = "Read and change the design topics in docs/design/, one topic per subject."
K_EXIT_FINDINGS = 1


def register_design_commands(
    app: "typer.Typer",
    *,
    program: str,
    panel: str,
    project_root: Callable[[], Path],
    report: Callable[[str], None] = print,
    group_cls: type | None = None,
) -> None:
    """Adds the `design` group to *app*.

    Args:
        app: The application to add the group to.
        program: The command the user types, for the examples.
        panel: The help panel the group is listed under.
        project_root: Returns the repository root; called when a command runs.
        report: Prints one line of the result the way the CLI prints.
        group_cls: The Click group class the CLI draws its help with.
    """
    import typer

    options: dict = {"help": K_HELP, "no_args_is_help": True, "rich_markup_mode": "rich"}
    if group_cls is not None:
        options["cls"] = group_cls
    design_app = typer.Typer(**options)

    def store() -> DesignStore:
        """Returns the design store of the repository the CLI runs in."""
        return DesignStore(project_root())

    json_option = typer.Option(False, "--json", help="Print JSON, for an agent.")

    @design_app.command("list", epilog=f"{program} design list --json")
    def list_topics(as_json: bool = json_option) -> None:
        """List every topic with its status, its modules and its open phases."""
        topics = store().topics()
        payload = [
            {
                "topic": topic.name,
                "status": topic.document.status.removeprefix("**Status:** "),
                "modules": topic.document.modules(),
                "open_phases": [p.ident for p in topic.document.phases if p.state not in K_CLOSED_PHASE_STATES],
                "revision": topic.is_under_revision(),
            }
            for topic in topics
        ]
        if as_json:
            report(json.dumps(payload, indent=2))
            return
        for item in payload:
            modules = ", ".join(item["modules"] or []) or "none"
            report(f"{item['topic']}: {item['status']} [{modules}]")

    @design_app.command("show", epilog=f"{program} design show PHYSICS")
    def show(name: str = typer.Argument(..., help="The topic.")) -> None:
        """Print a topic's document and list its pages."""
        topic = store().topic(name)
        report(topic.path.read_text(encoding="utf-8-sig").rstrip("\n"))
        if topic.path.name == "README.md":
            pages = sorted(p.name for p in topic.path.parent.glob("*.md") if p.name != "README.md")
            report("")
            report(f"pages: {', '.join(pages) or 'none'}")

    @design_app.command("owner", epilog=f"{program} design owner modules/physics/source/step.cpp")
    def owner(path: str = typer.Argument(..., help="A path from the repository root.")) -> None:
        """Print the topic that owns the module holding a path, or none."""
        report(store().owner(path) or "none")

    @design_app.command("new", epilog=f"{program} design new ATMOSPHERE --modules modules/atmosphere --about \"The air, its scattering and its clouds\"")
    def new(
        name: str = typer.Argument(..., help="The topic, upper case words joined by _."),
        modules: str = typer.Option(..., "--modules", help="The module paths it owns, separated by commas, or none."),
        about: str = typer.Option(..., "--about", help="One sentence saying what the topic is."),
    ) -> None:
        """Open a topic; refuses a module another topic owns."""
        current = store()
        path = current.create(name, modules=split_values(modules), about=about)
        report(current.relative(path))

    @design_app.command("page", epilog=f"{program} design page ATMOSPHERE CLOUDS")
    def page(
        name: str = typer.Argument(..., help="The topic."),
        page_name: str = typer.Argument(..., help="The page, upper case words joined by _."),
    ) -> None:
        """Add a page beside a topic's README.md."""
        current = store()
        report(current.relative(current.add_page(name, page_name)))

    @design_app.command("phase", epilog=f"{program} design phase ATMOSPHERE A3 \"Clouds cast shadows\"")
    def phase(
        name: str = typer.Argument(..., help="The topic."),
        ident: str = typer.Argument(..., help="The phase id."),
        text: str = typer.Argument(..., help="What the phase delivers."),
    ) -> None:
        """Add a planned phase to a topic."""
        added = store().add_phase(name, ident, text)
        report(f"{name}#{added.ident} planned")

    @design_app.command("phase-state", epilog=f"{program} design phase-state ATMOSPHERE A3 built")
    def phase_state(
        name: str = typer.Argument(..., help="The topic."),
        ident: str = typer.Argument(..., help="The phase id."),
        state: str = typer.Argument(..., help="planned, building, built or withdrawn."),
    ) -> None:
        """Move a phase to a state; the topic ships when every phase is built or withdrawn."""
        report(store().set_phase_state(name, ident, state))

    @design_app.command("overlap", epilog=f"{program} design overlap")
    def overlap(as_json: bool = json_option) -> None:
        """List modules two topics name, nested modules, and topic names that share a word."""
        found = find_overlap(store())
        if as_json:
            report(json.dumps({
                "shared": [{"module": m, "topics": list(t)} for m, t in found.shared],
                "nested": [{"outer": o, "outer_topic": a, "inner": i, "inner_topic": b} for o, a, i, b in found.nested],
                "words": [{"topics": [a, b], "word": w} for a, b, w in found.words],
            }, indent=2))
            return
        for module, topics in found.shared:
            report(f"shared {module}: {', '.join(topics)}")
        for outer, first, inner, second in found.nested:
            report(f"nested {inner} ({second}) inside {outer} ({first})")
        for first, second, word in found.words:
            report(f"word {word}: {first}, {second}")
        if not (found.shared or found.nested or found.words):
            report("no overlap")

    @design_app.command("merge", epilog=f"{program} design merge ATMOSPHERE VOLUMETRIC_CLOUDS")
    def merge(
        into: str = typer.Argument(..., help="The topic that stays."),
        source: str = typer.Argument(..., help="The topic that becomes its page."),
    ) -> None:
        """Make one topic a page of another, join their phases and modules, and rewrite citations."""
        current = store()
        result = TopicMerger(current).merge(into, source)
        report(current.relative(result.page))
        for old, new in result.renamed_phases:
            report(f"phase {source}#{old} -> {into}#{new}")
        unplaced = [r for r in result.rewrites if r.new is None]
        report(f"citations rewritten: {len(result.rewrites) - len(unplaced)}")
        for rewrite in unplaced:
            report(f"cannot place {current.relative(rewrite.path)}:{rewrite.line}: {rewrite.old}")

    @design_app.command("check", epilog=f"{program} design check")
    def check() -> None:
        """Check every topic against the format and the ownership rule; exits 1 on a finding."""
        root = project_root()
        findings = check_design(DesignStore(root))
        for finding in findings:
            report(f"{_shown(finding.path, root)}:{finding.line}: {finding.message}")
        if findings:
            raise typer.Exit(K_EXIT_FINDINGS)
        report("clean")

    app.add_typer(design_app, name=K_DESIGN, rich_help_panel=panel)


def _shown(path: Path, root: Path) -> str:
    """Returns a path from the root when it is under it."""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)
