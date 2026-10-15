# aliases.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Old spellings of a CLI's commands: they still run, hidden, and say what replaced them.

A CLI declares one :class:`AliasTable` and registers each old word through it. The table
prints one notice per process, to a terminal only, and lists the rows whose date has passed.
"""

from __future__ import annotations

import functools
import os
import sys
from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Any, Callable, Iterable, TextIO

from .errors import SushiCoreError

if TYPE_CHECKING:
    import typer

K_NOTICE_SWITCH_SUFFIX = "_NO_DEPRECATION_NOTICE"


class UnknownAliasError(SushiCoreError):
    """Reports an old spelling the alias table does not hold."""


@dataclass(frozen=True, slots=True)
class Alias:
    """Holds one old spelling, the spelling that replaces it and its last day.

    @param old The command line still accepted, e.g. ``sr doxygen``.
    @param new The command line that replaces it, e.g. ``sr docs``.
    @param removed_after The last day the old spelling works; None for a permanent alias.
    """

    old: str
    new: str
    removed_after: date | None


class AliasTable:
    """Holds one CLI's old spellings and announces them.

    @param program The command the user types, e.g. ``sr``; it prefixes the notice and
                   names the environment switch ``SR_NO_DEPRECATION_NOTICE``.
    @param aliases The rows of the table.
    """

    __slots__ = ("_program", "_by_old", "_announced")

    def __init__(self, program: str, aliases: Iterable[Alias]) -> None:
        self._program = program
        self._by_old = {alias.old: alias for alias in aliases}
        self._announced = False

    @property
    def notice_switch(self) -> str:
        """Returns the environment variable that silences the notice when it holds ``1``."""
        return self._program.upper() + K_NOTICE_SWITCH_SUFFIX

    def alias_for(self, old: str) -> Alias:
        """Returns the row whose old spelling is *old*.

        Raises:
            UnknownAliasError: No row carries that spelling.
        """
        try:
            return self._by_old[old]
        except KeyError as error:
            raise UnknownAliasError(f"no alias for `{old}`") from error

    def notice(self, alias: Alias) -> str:
        """Returns the one line that tells the user *alias*'s new spelling and last day."""
        line = f"{self._program}: `{alias.old}` is now `{alias.new}`"
        if alias.removed_after is None:
            return line + "."
        return f"{line}; the old spelling is removed after {alias.removed_after.isoformat()}."

    def announce(self, alias: Alias, *, stream: TextIO | None = None) -> None:
        """Prints *alias*'s notice once per table, to a terminal, unless it is switched off."""
        target = sys.stderr if stream is None else stream
        if self._announced or alias.removed_after is None:
            return
        if os.environ.get(self.notice_switch) == "1" or not target.isatty():
            return
        print(self.notice(alias), file=target)
        self._announced = True

    def deprecated(self, callback: Callable[..., Any], old: str) -> Callable[..., Any]:
        """Returns *callback* wrapped to announce the alias for *old* first, signature kept."""
        alias = self.alias_for(old)

        @functools.wraps(callback)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Announces the alias, then runs the wrapped callback."""
            self.announce(alias)
            return callback(*args, **kwargs)

        return wrapper

    def command(
        self, parent: "typer.Typer", word: str, callback: Callable[..., Any], old: str,
        *, hidden: bool = True, **options: Any,
    ) -> None:
        """Registers *word* under *parent* as the old spelling *old* of *callback*'s command.

        Args:
            parent: The application or sub-application the old word answers under.
            word: The old command word.
            callback: The function of the command that replaces it.
            old: The full old spelling, a key of this table.
            hidden: False when the parent itself is hidden and the word should list there.
            options: Passed to ``parent.command``, e.g. ``context_settings``.
        """
        parent.command(word, hidden=hidden, **options)(self.deprecated(callback, old))

    def expired(self, today: date) -> list[Alias]:
        """Returns every row whose last day lies before *today*."""
        return [alias for alias in self._by_old.values()
                if alias.removed_after is not None and alias.removed_after < today]
