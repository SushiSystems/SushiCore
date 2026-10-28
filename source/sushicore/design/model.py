# model.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The frame of a design topic: its title, status line, metadata, five sections and phase table.

The tool writes the frame; the prose inside a section is the author's. The rules are in
`docs/reference/DESIGN.md`.
"""

from __future__ import annotations

import datetime
import re
from dataclasses import dataclass, field

from .errors import DesignError

K_SECTIONS = ("Problem", "Decision", "Design", "Phases", "Open questions")
K_PHASES = "Phases"
K_PHASE_COLUMNS = ("Id", "Phase", "State")
K_PHASE_STATES = ("planned", "building", "built", "withdrawn")
K_CLOSED_PHASE_STATES = frozenset({"built", "withdrawn"})
K_NONE = "none"
K_NO_PHASES = "None."
K_STATUS_CEILING = 160
K_ABOUT_FIELD = "About"
K_MODULES_FIELD = "Modules"
K_IMPLEMENTS_FIELD = "Implements"
K_DESIGNS_FIELD = "Designs"
K_STATUS_PREFIX = "**Status:** "
K_TOPIC_NAME = re.compile(r"^[A-Z][A-Z0-9_]*$")
K_PHASE_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]*$")
K_FIELD = re.compile(r"^\*\*(?P<name>[A-Za-z][A-Za-z ]*):\*\*\s*(?P<value>.*?)\s*$")
K_FENCE = re.compile(r"^(`{3,}|~{3,})")
K_SECTION = re.compile(r"^## (\S.*?)\s*$")
K_TABLE_ROW = re.compile(r"^\|(.*)\|\s*$")
K_TABLE_RULE = re.compile(r"^\|[\s:|-]+\|\s*$")
K_STATUS_FORMS = re.compile(
    r"^\*\*Status:\*\* (?:(?P<open>Open) — \S"
    r"|Shipped — (?P<shipped>\d{4}-\d{2}-\d{2})(?:$|\. \S)"
    r"|Superseded — (?P<superseded>\d{4}-\d{2}-\d{2}) by \S"
    r"|Withdrawn — (?P<withdrawn>\d{4}-\d{2}-\d{2}), \S)"
)


@dataclass(frozen=True, slots=True)
class Phase:
    """One row of a phase table."""

    ident: str
    text: str
    state: str
    line: int = 0


@dataclass(slots=True)
class TopicDocument:
    """A topic's README.md read into its frame, with the line each part sits on."""

    title: str
    status: str
    status_line: int
    fields: dict[str, tuple[int, str]] = field(default_factory=dict)
    sections: list[tuple[int, str]] = field(default_factory=list)
    phases: list[Phase] = field(default_factory=list)
    phase_header: tuple[int, tuple[str, ...]] | None = None
    phase_faults: list[tuple[int, str]] = field(default_factory=list)

    def modules(self) -> list[str] | None:
        """Returns the module paths of the Modules line; [] for `none`, None without the line."""
        found = self.fields.get(K_MODULES_FIELD)
        return None if found is None else split_values(found[1])

    def is_open(self) -> bool:
        """Returns whether the status line is of the Open form."""
        match = K_STATUS_FORMS.match(self.status)
        return bool(match and match["open"])


def is_topic_name(name: str) -> bool:
    """Returns whether a name can be a topic: upper case words joined by underscores."""
    return bool(K_TOPIC_NAME.match(name))


def split_values(value: str) -> list[str]:
    """Returns the comma separated items of a metadata value, without code marks and `none`."""
    items = (item.strip().strip("`").strip() for item in value.split(","))
    return [item for item in items if item and item.lower() != K_NONE]


def body_lines(text: str) -> list[tuple[int, str]]:
    """Returns the number and text of each line outside fenced blocks."""
    kept: list[tuple[int, str]] = []
    fence = ""
    for number, line in enumerate(text.splitlines(), start=1):
        opener = K_FENCE.match(line.lstrip())
        if fence:
            fence = "" if opener and opener.group(1).startswith(fence) else fence
        elif opener:
            fence = opener.group(1)
        else:
            kept.append((number, line))
    return kept


def table_cells(line: str) -> list[str]:
    """Returns the trimmed cells of a table row."""
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def parse_topic(text: str) -> TopicDocument:
    """Returns the frame of a topic document."""
    lines = text.splitlines()
    title = lines[0][2:].strip() if lines and lines[0].startswith("# ") else ""
    status_line, status = 1, ""
    for number, line in enumerate(lines[1:], start=2):
        if line.strip():
            status_line, status = number, line
            break
    document = TopicDocument(title, status, status_line)
    for number, line in enumerate(lines[status_line:], start=status_line + 1):
        if not line.strip():
            continue
        match = K_FIELD.match(line)
        if match is None:
            break
        document.fields[match["name"]] = (number, match["value"])
    inside_phases = False
    rows: list[tuple[int, str]] = []
    for number, line in body_lines(text):
        heading = K_SECTION.match(line)
        if heading:
            document.sections.append((number, heading.group(1)))
            inside_phases = heading.group(1) == K_PHASES
        elif inside_phases and K_TABLE_ROW.match(line):
            rows.append((number, line))
    _read_phases(document, rows)
    return document


def render_topic(title: str, about: str, modules: list[str], phases: list[Phase]) -> str:
    """Returns a new topic document: the status line, the metadata and the five sections."""
    module_value = ", ".join(f"`{path}`" for path in modules) if modules else K_NONE
    lines = [
        f"# {title}",
        "",
        f"{K_STATUS_PREFIX}{open_status(phases)}",
        f"**{K_ABOUT_FIELD}:** {about}",
        f"**{K_MODULES_FIELD}:** {module_value}",
        "",
    ]
    for section in K_SECTIONS:
        lines += [f"## {section}", ""]
        if section == K_PHASES:
            lines += [*phase_table(phases), ""] if phases else [K_NO_PHASES, ""]
        else:
            lines += [K_NO_PHASES, ""]
    return "\n".join(lines).rstrip("\n") + "\n"


def open_status(phases: list[Phase]) -> str:
    """Returns the Open form of the status line, naming the phases still to be built."""
    remaining = [phase.ident for phase in phases if phase.state not in K_CLOSED_PHASE_STATES]
    if not remaining:
        return "Open — no phase planned yet"
    return "Open — phases " + ", ".join(remaining) + " to be built"


def shipped_status(today: datetime.date) -> str:
    """Returns the Shipped form of the status line."""
    return f"Shipped — {today.isoformat()}"


def phase_table(phases: list[Phase]) -> list[str]:
    """Returns the lines of a phase table."""
    lines = ["| " + " | ".join(K_PHASE_COLUMNS) + " |", "| --- | --- | --- |"]
    lines += [f"| {phase.ident} | {phase.text.replace('|', '/')} | {phase.state} |" for phase in phases]
    return lines


def replace_phases(text: str, phases: list[Phase]) -> str:
    """Returns the document with its phase table, or the `None.` that stands for one, replaced.

    @throws DesignError When the document has no Phases section.
    """
    lines = text.split("\n")
    heading = next((index for index, line in enumerate(lines) if line.strip() == f"## {K_PHASES}"), None)
    if heading is None:
        raise DesignError(f"the document has no '## {K_PHASES}' section")
    end = next(
        (index for index in range(heading + 1, len(lines)) if K_SECTION.match(lines[index])),
        len(lines),
    )
    body = lines[heading + 1:end]
    first = next(
        (index for index, line in enumerate(body) if K_TABLE_ROW.match(line) or line.strip() == K_NO_PHASES),
        None,
    )
    table = phase_table(phases)
    if first is None:
        body = ["", *table, *body]
    else:
        last = first
        while last + 1 < len(body) and K_TABLE_ROW.match(body[last + 1]):
            last += 1
        body = [*body[:first], *table, *body[last + 1:]]
    return "\n".join([*lines[: heading + 1], *body, *lines[end:]])


def replace_status(text: str, status: str) -> str:
    """Returns the document with its status line replaced."""
    lines = text.split("\n")
    for index, line in enumerate(lines):
        if line.startswith(K_STATUS_PREFIX):
            lines[index] = f"{K_STATUS_PREFIX}{status}"
            break
    return "\n".join(lines)


def replace_field(text: str, name: str, value: str) -> str:
    """Returns the document with a metadata line set, added under the status line when missing."""
    lines = text.split("\n")
    marker = f"**{name}:**"
    for index, line in enumerate(lines):
        if line.startswith(marker):
            lines[index] = f"{marker} {value}"
            return "\n".join(lines)
    for index, line in enumerate(lines):
        if line.startswith(K_STATUS_PREFIX):
            lines.insert(index + 1, f"{marker} {value}")
            break
    return "\n".join(lines)


def _read_phases(document: TopicDocument, rows: list[tuple[int, str]]) -> None:
    """Reads the first table of the Phases section into the document's phases."""
    if not rows:
        return
    number, header = rows[0]
    document.phase_header = (number, tuple(table_cells(header)))
    if document.phase_header[1] != K_PHASE_COLUMNS:
        return
    for number, line in rows[1:]:
        if K_TABLE_RULE.match(line):
            continue
        cells = table_cells(line)
        if len(cells) != len(K_PHASE_COLUMNS):
            document.phase_faults.append((number, "a phase row has the cells Id, Phase and State"))
            continue
        document.phases.append(Phase(cells[0].strip("`* "), cells[1], cells[2].strip("`"), number))
