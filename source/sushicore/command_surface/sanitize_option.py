# sanitize_option.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Declares the shared ``--sanitize`` option, a comma list of the sanitizers ``SushiSanitizers`` takes."""

from __future__ import annotations

from typing import Optional, Sequence

from .command_parameter import CommandParameter
from .errors import SanitizerConflictError, UnknownSanitizerError

K_SANITIZE_FLAG = "--sanitize"
K_ADDRESS = "address"
K_UNDEFINED = "undefined"
K_THREAD = "thread"

#: The sanitizers ``sushi_sanitizers`` builds, in the order a parsed set is returned.
K_SANITIZER_KINDS = (K_ADDRESS, K_UNDEFINED, K_THREAD)

#: The pairs one build cannot carry together.
K_SANITIZER_CONFLICTS = (frozenset({K_ADDRESS, K_THREAD}),)


def parse_sanitizers(text: Optional[str], allowed: Sequence[str] = K_SANITIZER_KINDS) -> tuple[str, ...]:
    """Returns the sanitizers a ``--sanitize`` value names, once each, in the order of *allowed*.

    An absent or empty value names none. The joined result is the ``<PREFIX>_SANITIZE`` cache entry
    ``sushi_sanitizers`` reads, so ``undefined,address`` and ``address,undefined`` give one tree.

    Args:
        text: The value, such as ``address,undefined``.
        allowed: The sanitizers the command builds; a subset of ``K_SANITIZER_KINDS``.

    Raises:
        UnknownSanitizerError: A name is not in *allowed*.
        SanitizerConflictError: Two names cannot share one build, as address and thread cannot.
    """
    names = {name.strip() for name in (text or "").split(",") if name.strip()}
    unknown = sorted(names.difference(allowed))
    if unknown:
        raise UnknownSanitizerError(
            f"--sanitize takes {', '.join(allowed)}, comma-separated; {', '.join(unknown)} is not one.")
    for conflict in K_SANITIZER_CONFLICTS:
        if conflict <= names:
            raise SanitizerConflictError(
                f"--sanitize cannot combine {' and '.join(sorted(conflict))} in one build.")
    return tuple(name for name in allowed if name in names)


def sanitize_option(allowed: Sequence[str] = K_SANITIZER_KINDS) -> CommandParameter:
    """Returns the ``--sanitize`` parameter, named ``sanitize``, whose value is checked as it is parsed.

    Args:
        allowed: The sanitizers the command builds; a subset of ``K_SANITIZER_KINDS``.

    Raises:
        UnknownSanitizerError: *allowed* names a sanitizer ``sushi_sanitizers`` does not build.
    """
    import typer

    foreign = sorted(set(allowed).difference(K_SANITIZER_KINDS))
    if foreign:
        raise UnknownSanitizerError(
            f"sushi_sanitizers builds {', '.join(K_SANITIZER_KINDS)}; {', '.join(foreign)} is not one.")
    conflicts = [" and ".join(sorted(pair)) for pair in K_SANITIZER_CONFLICTS if pair <= set(allowed)]
    rule = "".join(f"; {pair} do not combine" for pair in conflicts)

    def check(value: Optional[str]) -> Optional[str]:
        """Refuses a value that ``parse_sanitizers`` refuses, as a usage error."""
        try:
            parse_sanitizers(value, allowed)
        except (UnknownSanitizerError, SanitizerConflictError) as error:
            raise typer.BadParameter(str(error)) from error
        return value

    return CommandParameter(
        name="sanitize",
        annotation=Optional[str],
        default=typer.Option(
            None, K_SANITIZE_FLAG, metavar="KINDS", callback=check,
            help="Sanitizers for host code, comma-separated: " + ", ".join(allowed) + ". "
                 "Each set builds in a tree of its own" + rule + "."),
    )
