# check.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Every rule `design check` enforces: the frame of each topic, its metadata and module ownership.

The rules are in `docs/reference/DESIGN.md`, section "Check".
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path

from .model import (
    K_ABOUT_FIELD,
    K_DESIGNS_FIELD,
    K_IMPLEMENTS_FIELD,
    K_MODULES_FIELD,
    K_NO_PHASES,
    K_PHASE_COLUMNS,
    K_PHASE_STATES,
    K_PHASES,
    K_SECTIONS,
    K_STATUS_CEILING,
    body_lines,
    parse_topic,
    split_values,
)
from .store import DesignStore, Topic

K_HASH = re.compile(r"(?<![\w/.-])[0-9a-f]{7,40}(?![\w/-])")
K_HASH_DIGIT = re.compile(r"\d")
K_HASH_LETTER = re.compile(r"[a-f]")
K_EXECUTION_VERB = r"(?:built|landed|merged|shipped|completed|implemented|reviewed|finished|done)"
K_ISO_DATE = r"\d{4}-\d{2}-\d{2}"
K_EXECUTION_RECORD = re.compile(
    rf"\b{K_EXECUTION_VERB}\b[^.\n]{{0,60}}{K_ISO_DATE}|{K_ISO_DATE}[^.\n]{{0,40}}\b{K_EXECUTION_VERB}\b",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class Finding:
    """A line of a design document that breaks a rule."""

    path: Path
    line: int
    message: str


@dataclass(slots=True)
class DesignCheck:
    """What one run of the check reads, read once and shared by the rules."""

    store: DesignStore
    topics: list[Topic]


def rule_topic_folder(check: DesignCheck) -> Iterator[Finding]:
    """Yields a finding for a document that sits loose in docs/design."""
    for path in check.store.loose_documents():
        yield Finding(path, 1, f"a topic is a folder: move it to {path.stem}/README.md")


def rule_sections(check: DesignCheck) -> Iterator[Finding]:
    """Yields a finding for a section that is not one of the five, one missing, and a wrong order."""
    for topic in check.topics:
        names = [name for _, name in topic.document.sections]
        for number, name in topic.document.sections:
            if name not in K_SECTIONS:
                yield Finding(topic.path, number, f"'## {name}' is not one of the sections: {', '.join(K_SECTIONS)}")
        for name in K_SECTIONS:
            if name not in names:
                yield Finding(topic.path, 1, f"the section '## {name}' is missing")
        known = [name for name in names if name in K_SECTIONS]
        if len(set(known)) == len(K_SECTIONS) and known != list(K_SECTIONS):
            yield Finding(topic.path, 1, f"the sections are in the order {', '.join(K_SECTIONS)}")


def rule_status_length(check: DesignCheck) -> Iterator[Finding]:
    """Yields a finding for a status line longer than the ceiling."""
    for topic in check.topics:
        length = len(topic.document.status)
        if length > K_STATUS_CEILING:
            yield Finding(topic.path, topic.document.status_line, f"status is {length} characters; the ceiling is {K_STATUS_CEILING}")


def rule_phase_table(check: DesignCheck) -> Iterator[Finding]:
    """Yields a finding for a Phases section without its table, with other columns, or an unknown state."""
    for topic in check.topics:
        document = topic.document
        heading = next((number for number, name in document.sections if name == K_PHASES), None)
        if heading is None:
            continue
        if document.phase_header is None:
            text = topic.path.read_text(encoding="utf-8-sig")
            if K_NO_PHASES not in _section_text(text, K_PHASES):
                yield Finding(topic.path, heading, f"'## {K_PHASES}' holds a table of {', '.join(K_PHASE_COLUMNS)}, or '{K_NO_PHASES}'")
            continue
        number, columns = document.phase_header
        if columns != K_PHASE_COLUMNS:
            yield Finding(topic.path, number, f"the phase table has the columns {', '.join(K_PHASE_COLUMNS)}")
            continue
        for line, message in document.phase_faults:
            yield Finding(topic.path, line, message)
        for phase in document.phases:
            if phase.state not in K_PHASE_STATES:
                yield Finding(topic.path, phase.line, f"a phase state is one of {', '.join(K_PHASE_STATES)}")


def rule_no_commit_hashes(check: DesignCheck) -> Iterator[Finding]:
    """Yields a finding for each commit hash in a design document."""
    for topic in check.topics:
        for number, line in body_lines(topic.path.read_text(encoding="utf-8-sig")):
            for match in K_HASH.finditer(line):
                if K_HASH_DIGIT.search(match.group()) and K_HASH_LETTER.search(match.group()):
                    yield Finding(topic.path, number, "a commit hash belongs in the work folder's REPORT.md")


def rule_no_execution_record(check: DesignCheck) -> Iterator[Finding]:
    """Yields a finding for each line outside the status that dates when work was done."""
    for topic in check.topics:
        for number, line in body_lines(topic.path.read_text(encoding="utf-8-sig")):
            if number != topic.document.status_line and K_EXECUTION_RECORD.search(line):
                yield Finding(topic.path, number, "when work was done belongs in the work folder's REPORT.md")


def rule_modules_required(check: DesignCheck) -> Iterator[Finding]:
    """Yields a finding for a topic without a Modules line, and a `none` without an About line."""
    for topic in check.topics:
        modules = topic.document.modules()
        if modules is None:
            yield Finding(topic.path, 1, f"a topic names its modules on a '**{K_MODULES_FIELD}:**' line, or none")
        elif not modules and K_ABOUT_FIELD not in topic.document.fields:
            yield Finding(topic.path, 1, f"a topic of no module says what it is on an '**{K_ABOUT_FIELD}:**' line")


def rule_modules_exist(check: DesignCheck) -> Iterator[Finding]:
    """Yields a finding for each module path that is not in the repository."""
    for topic in check.topics:
        found = topic.document.fields.get(K_MODULES_FIELD)
        for module in topic.document.modules() or []:
            if not (check.store.root / module).exists():
                yield Finding(topic.path, found[0] if found else 1, f"the module '{module}' is not in the repository")


def rule_module_owner(check: DesignCheck) -> Iterator[Finding]:
    """Yields a finding for each module two topics name: a module belongs to one topic."""
    for module, names in sorted(check.store.owners().items()):
        if len(names) < 2:
            continue
        for topic in check.topics:
            if topic.name in names[1:]:
                found = topic.document.fields.get(K_MODULES_FIELD)
                yield Finding(
                    topic.path, found[0] if found else 1,
                    f"'{module}' is owned by {names[0]}; merge the topics with `design merge` or drop it here",
                )


def rule_work_references(check: DesignCheck) -> Iterator[Finding]:
    """Yields a finding for an Implements or Designs item of a work folder that names no topic or phase."""
    known = {topic.name: topic for topic in check.topics}
    for path in check.store.work_documents():
        fields = parse_topic(path.read_text(encoding="utf-8-sig")).fields
        for name in (K_IMPLEMENTS_FIELD, K_DESIGNS_FIELD):
            found = fields.get(name)
            if found is None:
                continue
            number, value = found
            for item in split_values(value):
                topic, _, phase = (part.strip() for part in item.partition("#"))
                if topic not in known:
                    yield Finding(path, number, f"'{topic}' is not a design topic")
                elif name == K_IMPLEMENTS_FIELD and not phase:
                    yield Finding(path, number, f"'{item}' names a topic and no phase; write TOPIC#PHASE")
                elif phase and phase not in {p.ident for p in known[topic].document.phases}:
                    yield Finding(path, number, f"'{topic}' has no phase '{phase}'")


K_RULES: dict[str, Callable[[DesignCheck], Iterator[Finding]]] = {
    "topic_folder": rule_topic_folder,
    "sections": rule_sections,
    "status_length": rule_status_length,
    "phase_table": rule_phase_table,
    "no_commit_hashes": rule_no_commit_hashes,
    "no_execution_record": rule_no_execution_record,
    "modules_required": rule_modules_required,
    "modules_exist": rule_modules_exist,
    "module_owner": rule_module_owner,
    "work_references": rule_work_references,
}


def check_design(store: DesignStore, rules: list[str] | None = None) -> list[Finding]:
    """Returns every finding of a repository's design topics, or of the named rules only."""
    check = DesignCheck(store, store.topics())
    chosen = K_RULES if rules is None else {name: K_RULES[name] for name in rules}
    found: list[Finding] = []
    for rule in chosen.values():
        found += rule(check)
    return found


def _section_text(text: str, name: str) -> str:
    """Returns the lines under a `##` heading, up to the next one, outside fences."""
    kept: list[str] = []
    inside = False
    for _, line in body_lines(text):
        if line.startswith("## "):
            inside = line[3:].strip() == name
        elif inside:
            kept.append(line.strip())
    return "\n".join(kept)
