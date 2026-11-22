# adaptivecpp_compat.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""The private helpers ``sushicore.provision.toolchains.adaptivecpp`` exported before 0.17.0."""

from __future__ import annotations

import importlib
import logging
import threading
from collections.abc import Callable, Sequence
from pathlib import Path

from rich.text import Text

from ..default_console import DEFAULT_CONSOLE
from ...deprecated_name import warn_deprecated

_log = logging.getLogger(__name__)

#: Seconds to wait for consent before the heavy LLVM download; the default answer is no.
K_LLVM_CONSENT_TIMEOUT = 30

#: The answers that mean yes, in English and Turkish.
K_YES = ("y", "yes", "e", "evet")

#: The module that holds the Windows LLVM lookup; named, not imported, because it imports adaptivecpp.
K_WINDOWS_LLVM_MODULE = "sushicore.provision.llvm_plans.windows"


def find_windows_llvm(bases: Sequence[Path] | None = None) -> tuple[str, str] | None:
    """Return ``(LLVM_DIR, clang_prefix)`` for an existing Windows LLVM, else None.

    Deprecated: use ``sushicore.provision.llvm_plans.windows.find_windows_llvm``.
    """
    warn_deprecated("_find_windows_llvm", "sushicore.provision.llvm_plans.windows.find_windows_llvm")
    return importlib.import_module(K_WINDOWS_LLVM_MODULE).find_windows_llvm(bases)


def confirm_timeout(message: str, timeout: int = K_LLVM_CONSENT_TIMEOUT, default: bool = False, *,
                    reader: Callable[[], str] | None = None) -> bool:
    """Ask a yes/no question on the default console, returning *default* if unanswered in *timeout*.

    Deprecated: ask through the licence consent step, which names the licence and its link.

    Args:
        message: The question to print, as Rich markup.
        reader: Returns one line of the answer; ``input`` when omitted.
    """
    warn_deprecated("_confirm_timeout", "the licence consent step")
    console = DEFAULT_CONSOLE()
    if console.is_machine():
        answer = console.prompt(Text.from_markup(message).plain, "y" if default else "n")
        return answer.strip().lower() in K_YES
    console.console.print(message)
    hint = r"\[y/n]" if default is False else r"\[Y/n]"
    console.console.print(
        f"[bold]Your choice {hint}[/bold] (auto-{'yes' if default else 'no'} in {timeout}s): ",
        end="")
    result = [default]

    def read() -> None:
        """Store whether the answer line means yes."""
        try:
            result[0] = (reader or input)().strip().lower() in K_YES
        except (EOFError, OSError):
            _log.debug("no answer on stdin; keeping the default %s", default)

    thread = threading.Thread(target=read, daemon=True)
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        console.console.print()
        console.info(f"No answer in {timeout}s — defaulting to {'yes' if default else 'no'}.")
    return result[0]
