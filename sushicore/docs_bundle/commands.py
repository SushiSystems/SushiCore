# commands.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The `docs` command group, registered on a CLI from where its project and API are.

The behaviour of each invocation is in `docs/reference/DOCS_BUNDLE.md`.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional

from .api_reference import ApiSource
from .producer import K_DEFAULT_OUTPUT, BundleProducer, BundleRequest

if TYPE_CHECKING:
    import typer

K_API_HELP = "Build the API reference with Doxygen, or bundle the documentation."
K_BUNDLE_HELP = "Bundle the documentation."


def register_docs_commands(
    app: "typer.Typer",
    *,
    program: str,
    panel: str,
    project_root: Callable[[], Path],
    api: Callable[[], ApiSource] | None = None,
    report: Callable[[str], None] = print,
    group_cls: type | None = None,
) -> None:
    """Adds the `docs` group to *app*: the bare form when *api* is given, and `bundle`.

    Args:
        app: The application to add the group to.
        program: The command the user types, for the examples.
        panel: The help panel the group is listed under.
        project_root: Returns the repository root; called when a command runs.
        api: Returns how this CLI builds its API reference; None for a CLI that builds none.
        report: Prints one line of the result the way the CLI prints.
        group_cls: The Click group class the CLI draws its help with.
    """
    import typer

    options: dict = {
        "help": K_BUNDLE_HELP if api is None else K_API_HELP,
        "no_args_is_help": api is None,
        "rich_markup_mode": "rich",
    }
    if group_cls is not None:
        options["cls"] = group_cls
    docs_app = typer.Typer(**options)

    if api is not None:
        def docs(ctx) -> None:
            """Build the API reference with Doxygen, or bundle the documentation."""
            if ctx.invoked_subcommand is None:
                raise typer.Exit(api().build())

        # Typer reads the annotation when it registers; the name `typer` is local to this call.
        docs.__annotations__ = {"ctx": typer.Context, "return": None}
        docs_app.callback(invoke_without_command=True, epilog=f"{program} docs")(docs)

    @docs_app.command(
        "bundle",
        epilog=f"{program} docs bundle --release 1.2.3\n"
               f"{program} docs bundle --release 1.2.3 --out build/site",
    )
    def bundle(
        release: str = typer.Option(
            ..., "--release", help="The release the bundle is named after, as 1.2.3."),
        out: Optional[Path] = typer.Option(
            None, "--out", help="Where the archive is written. Defaults to build/docs/bundle."),
    ) -> None:
        """Bundle the published documentation for docs.sushisystems.io."""
        root = project_root()
        request = BundleRequest(
            repository_root=root,
            release=release,
            output_dir=out if out is not None else root / K_DEFAULT_OUTPUT,
            api=None if api is None else api(),
        )
        result = BundleProducer().produce(request)
        report(f"{result.archive} ({result.page_count} pages)")
        report(f"sha256 {result.sha256}")

    app.add_typer(docs_app, name="docs", rich_help_panel=panel)
