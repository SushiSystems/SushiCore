# licence_consent.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Holds the third-party licences a setup run needs and the user's consent to them."""

from __future__ import annotations

import typing
from dataclasses import dataclass

from .outcome import K_EXIT_FAILED, K_EXIT_USAGE

__all__ = [
    "ConsentDecision",
    "LicenceConsent",
    "Licence",
    "decide",
    "is_accepted",
]

#: Answers to the consent question that mean yes.
_YES = frozenset({"y", "yes"})


@typing.final
@dataclass(frozen=True, slots=True)
class Licence:
    """Names one third-party licence and the page that holds its text."""

    name: str
    link: str


@typing.final
@dataclass(frozen=True, slots=True)
class ConsentDecision:
    """Holds whether the run may install, the licences asked about and the refusal's exit code."""

    granted: bool
    licences: tuple[Licence, ...]
    code: int = 0


def decide(licences: typing.Sequence[Licence], *, machine: bool, accept_flag: bool,
           answer: bool | None) -> ConsentDecision:
    """Returns whether a run that needs *licences* may install them.

    Args:
        machine: Whether the run renders machine output; such a run is never asked.
        accept_flag: Whether ``--accept-licences`` was given.
        answer: The user's yes or no to the question; None when nobody was asked.
    """
    held = tuple(licences)
    if not held or accept_flag:
        return ConsentDecision(True, held)
    if machine:
        return ConsentDecision(False, held, K_EXIT_USAGE)
    if answer:
        return ConsentDecision(True, held)
    return ConsentDecision(False, held, K_EXIT_FAILED)


class _Console(typing.Protocol):
    """The console calls consent is asked through."""

    def info(self, msg: str) -> None:
        """Prints an information line."""

    def error(self, msg: str) -> None:
        """Prints an error line."""

    def prompt(self, message: str, default: str | None = None) -> str:
        """Asks a question and returns the answer."""

    def is_machine(self) -> bool:
        """Returns whether the console renders machine output."""


@typing.final
class LicenceConsent:
    """Asks for consent to a run's licences once and remembers the answer.

    Args:
        console: The console the licences are named and the question asked through.
        accept_flag: Whether ``--accept-licences`` was given.
    """

    def __init__(self, console: _Console, *, accept_flag: bool) -> None:
        """Store the console and the flag; nothing has been asked yet."""
        self._console = console
        self._accept_flag = accept_flag
        self._decision: ConsentDecision | None = None

    @property
    def decision(self) -> ConsentDecision | None:
        """Returns the decision of this run, or None before :meth:`request` ran."""
        return self._decision

    def request(self, licences: typing.Sequence[Licence]) -> ConsentDecision:
        """Names *licences*, asks for consent when needed and returns the decision.

        A second call returns the first decision without asking again.
        """
        if self._decision is not None:
            return self._decision
        machine = self._console.is_machine()
        answer = None
        if licences and not self._accept_flag and not machine:
            self._name(licences, self._console.info)
            reply = self._console.prompt("Accept these licences? [y/N]", "n")
            answer = reply.strip().lower() in _YES
        self._decision = decide(licences, machine=machine, accept_flag=self._accept_flag,
                                answer=answer)
        if not self._decision.granted:
            self._refuse(self._decision)
        return self._decision

    def accepts(self, licence: Licence) -> bool:
        """Returns whether the user consented to *licence* in this run."""
        held = self._decision
        return held is not None and held.granted and licence in held.licences

    def _refuse(self, decision: ConsentDecision) -> None:
        """Names every licence of a refused run and says how to accept them."""
        self._console.error("Setup installs nothing without consent to these licences:")
        self._name(decision.licences, self._console.error)
        if decision.code == K_EXIT_USAGE:
            self._console.error("Read them, then re-run with --accept-licences.")

    @staticmethod
    def _name(licences: typing.Sequence[Licence], say: typing.Callable[[str], None]) -> None:
        """Prints one line per licence with its link."""
        for licence in licences:
            say(f"  {licence.name}: {licence.link}")


def is_accepted(consent: LicenceConsent | None, licence: Licence) -> bool:
    """Returns whether *consent* covers *licence*; False when the run holds no consent."""
    return consent is not None and consent.accepts(licence)
