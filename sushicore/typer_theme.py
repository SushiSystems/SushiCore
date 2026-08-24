"""Recolor Typer/Click's rich-powered ``--help`` screen to match the theme.

Typer (with ``rich_markup_mode="rich"``) renders ``--help`` through Rich, but
not via a ``Theme`` object — it reads a set of module-level style constants in
``typer.rich_utils`` at render time. There is no config seam to plug into, so
monkeypatching those constants at startup is the only way to make ``--help``
match everything else this package themes. This is why the coloring lives in
its own module: it is the one part of sushicore that reaches into another
package's internals instead of composing a clean abstraction.
"""

from __future__ import annotations

from .theme import Theme


def apply_typer_theme(theme: Theme) -> None:
    """Point Typer's help-screen colors at ``theme``. No-op if Typer isn't installed."""
    try:
        import typer.rich_utils as rich_utils
    except ImportError:
        return

    rich_utils.STYLE_USAGE_COMMAND = theme.header
    rich_utils.STYLE_OPTION = theme.cmd
    rich_utils.STYLE_SWITCH = theme.success
    rich_utils.STYLE_METAVAR = theme.warn
    rich_utils.STYLE_COMMANDS_TABLE_FIRST_COLUMN = theme.cmd
    rich_utils.STYLE_NEGATIVE_OPTION = theme.error
    rich_utils.STYLE_NEGATIVE_SWITCH = theme.error
    rich_utils.STYLE_REQUIRED_SHORT = theme.error
    rich_utils.STYLE_REQUIRED_LONG = f"dim {theme.error}"
    rich_utils.STYLE_ERRORS_PANEL_BORDER = theme.error
    rich_utils.STYLE_ABORTED = theme.error
    rich_utils.STYLE_DEPRECATED = theme.error
