# citations.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Finds the files of a repository that cite a document or an entry, and rewrites those citations.

A citation is a path to a document, a Markdown link to one, or the ID of a backlog entry. The
backlog and the design commands call this module when a document moves or an ID changes.
"""

from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

K_EXTENSIONS = frozenset({
    ".md", ".cpp", ".hpp", ".h", ".py", ".ts", ".tsx", ".glsl", ".comp", ".toml", ".json",
    ".txt", ".cmake",
})
K_SKIPPED_FOLDERS = frozenset({".git", "third_party", "node_modules", "build", ".venv"})
K_SKIPPED_TREES = (
    Path("docs") / "archive",
    *(Path("tools") / name for name in (
        "checking", "documentation", "layering", "licensing", "logs", "routing", "testing",
        "tests",
    )),
)
K_REVISION_FOLDER = "_REVISION"
K_README = "README.md"
K_DESIGN_PATH = re.compile(
    r"(?<![A-Za-z0-9_.-])(?P<docs>docs/)?design/"
    r"(?P<tail>[A-Za-z0-9_]+(?:\.md)?(?:/[A-Za-z0-9_.-]+)*)"
)
K_LINK = re.compile(r"\]\((?P<target>[A-Za-z0-9_./-]+)(?P<anchor>#[^)\s]*)?\)")
K_ENTRY_ID = re.compile(
    r"(?<![\w-])(?:(?P<owner>[a-z0-9][a-z0-9_.-]*) )?(?P<id>(?:RW|KI)-\d+)(?![\w-])"
)
K_EXIT_SOME_IGNORED = 0
K_EXIT_NONE_IGNORED = 1


@dataclass(frozen=True, slots=True)
class Rewrite:
    """One citation, the line it is on, and its replacement, or None when it cannot be placed."""

    path: Path
    line: int
    old: str
    new: str | None


def citing_files(root: Path) -> list[Path]:
    """Returns each file below *root* that may cite a document: not ignored, vendored or archived.

    The shared checkers and their tests write citations as fixtures, so they are left out.
    """
    found: list[Path] = []
    for folder, names, files in os.walk(root):
        names[:] = [name for name in names if name not in K_SKIPPED_FOLDERS]
        found += [Path(folder) / name for name in files if Path(name).suffix in K_EXTENSIONS]
    skipped = [(root / tree).resolve() for tree in K_SKIPPED_TREES]
    kept = [path for path in found if not any(tree in path.resolve().parents for tree in skipped)]
    return _drop_ignored(root, kept)


def rewrite_ids(text: str, renames: dict[str, str], foreign: frozenset[str]) -> tuple[str, int]:
    """Returns *text* with each ID of *renames* replaced, and how many were replaced.

    An ID written after the name of another repository, one of *foreign*, is that repository's
    and stays as it is.
    """
    count = 0

    def replace(match: re.Match[str]) -> str:
        """Returns the replacement of one ID, or the match when it is not renamed."""
        nonlocal count
        owner = match["owner"]
        if match["id"] not in renames or (owner is not None and owner in foreign):
            return match.group(0)
        count += 1
        prefix = "" if owner is None else f"{owner} "
        return f"{prefix}{renames[match['id']]}"

    return K_ENTRY_ID.sub(replace, text), count


def rewrite_id_citations(
    root: Path, renames: dict[str, str], *, apply: bool,
) -> list[Rewrite]:
    """Rewrites, or with *apply* False only lists, every citation of a renamed ID below *root*."""
    if not renames:
        return []
    foreign = frozenset(folder.name for folder in root.resolve().parent.iterdir() if folder.is_dir())
    foreign -= {root.resolve().name}
    found: list[Rewrite] = []
    for path in citing_files(root):
        text = _read(path)
        if text is None:
            continue
        fixed, count = rewrite_ids(text, renames, foreign)
        if count:
            found += _line_changes(path, text, fixed)
            if apply:
                path.write_text(fixed, encoding="utf-8", newline="")
    return found


def repair_text(
    path: Path,
    text: str,
    root: Path,
    topics: dict[str, Path],
    moves: dict[str, str] | None = None,
) -> tuple[str, list[Rewrite]]:
    """Returns *text* with each moved citation rewritten, and one Rewrite for each that was wrong.

    A move names a file below *root*, old to new, as paths from the root, and applies whether
    or not the old file is still there. A citation of a design document that is gone is
    rewritten to the topic that now holds it, found through *topics*, the document of each
    topic by name.
    """
    found: list[Rewrite] = []
    design = root / "docs" / "design"
    moved = moves or {}
    base = root.resolve()

    def line_of(position: int) -> int:
        """Returns the line a position of the text is on."""
        return text.count("\n", 0, position) + 1

    def fix_path(match: re.Match[str]) -> str:
        """Returns the replacement of a design path and records it when it was wrong."""
        tail = match["tail"].rstrip(".")
        suffix = match["tail"][len(tail):]
        prefix = match["docs"] or ""
        cited = f"{prefix}design/{tail}"
        if f"docs/design/{tail}" in moved:
            target = moved[f"docs/design/{tail}"]
            new = target if prefix else target.removeprefix("docs/")
            found.append(Rewrite(path, line_of(match.start()), cited, new))
            return f"{new}{suffix}"
        fixed = _placed(tail, root, topics)
        if fixed == tail:
            return match.group(0)
        new = None if fixed is None else f"{prefix}design/{fixed}"
        found.append(Rewrite(path, line_of(match.start()), cited, new))
        return match.group(0) if new is None else f"{new}{suffix}"

    def fix_link(match: re.Match[str]) -> str:
        """Returns the replacement of a relative link and records it when it was wrong."""
        target = (path.parent / match["target"]).resolve()
        below = target.relative_to(base).as_posix() if base in target.parents else ""
        anchor = match["anchor"] or ""
        if below in moved:
            new = os.path.relpath(root / moved[below], path.parent).replace(os.sep, "/")
            found.append(Rewrite(path, line_of(match.start()), match["target"], new))
            return f"]({new}{anchor})"
        former = None if target.exists() else _former_folder(path, design)
        earlier = None if former is None else (former / match["target"]).resolve()
        if earlier is not None and earlier.exists():
            new = os.path.relpath(earlier, path.parent.resolve()).replace(os.sep, "/")
            found.append(Rewrite(path, line_of(match.start()), match["target"], new))
            return f"]({new}{anchor})"
        if target.exists() or design.resolve() not in target.parents:
            return match.group(0)
        fixed = _placed(target.relative_to(design.resolve()).as_posix(), root, topics)
        if fixed is None:
            found.append(Rewrite(path, line_of(match.start()), match["target"], None))
            return match.group(0)
        new = os.path.relpath(design / fixed, path.parent).replace(os.sep, "/")
        found.append(Rewrite(path, line_of(match.start()), match["target"], new))
        return f"]({new}{anchor})"

    def fix_literal(match: re.Match[str]) -> str:
        """Returns the new path of a moved file cited outside docs/design."""
        new = moved[match.group(0)]
        found.append(Rewrite(path, line_of(match.start()), match.group(0), new))
        return new

    fixed = K_DESIGN_PATH.sub(fix_path, K_LINK.sub(fix_link, text))
    literal = [old for old in moved if not old.startswith("docs/design/")]
    if literal:
        pattern = re.compile(
            r"(?<![A-Za-z0-9_./-])(?:" + "|".join(re.escape(old) for old in literal) + r")"
            r"(?![A-Za-z0-9_/-])"
        )
        fixed = pattern.sub(fix_literal, fixed)
    return fixed, found


def repair_citations(
    root: Path,
    topics: dict[str, Path],
    moves: dict[str, str] | None = None,
    *,
    apply: bool,
    suffixes: frozenset[str] | None = None,
) -> list[Rewrite]:
    """Repairs, or with *apply* False only lists, every moved citation below *root*.

    With *suffixes*, only files of those suffixes are read, so a path a program holds as a
    value is never rewritten.
    """
    design = (root / "docs" / "design").resolve()
    found: list[Rewrite] = []
    for path in citing_files(root):
        if suffixes is not None and path.suffix not in suffixes:
            continue
        text = _read(path)
        if text is None:
            continue
        is_cited = any(Path(old).name in text for old in (moves or {}))
        if not is_cited and "design/" not in text and design not in path.resolve().parents:
            continue
        fixed, rewrites = repair_text(path, text, root, topics, moves)
        found += rewrites
        if apply and fixed != text:
            path.write_text(fixed, encoding="utf-8", newline="")
    return found


def files_citing(root: Path, cited: list[str], suffixes: frozenset[str]) -> list[Path]:
    """Returns each file of the given suffixes below *root* whose text names one of *cited*."""
    found: list[Path] = []
    for path in citing_files(root):
        if path.suffix not in suffixes:
            continue
        text = _read(path)
        if text is not None and any(name in text for name in cited):
            found.append(path)
    return found


def _placed(tail: str, root: Path, topics: dict[str, Path]) -> str | None:
    """Returns the tail below docs/design that now holds what *tail* named, or None."""
    design = root / "docs" / "design"
    if (design / tail).exists():
        return tail
    parts = tail.split("/")
    if parts[0] == K_REVISION_FOLDER:
        parts = parts[1:]
    if not parts:
        return None
    name = parts[0].removesuffix(".md")
    document = topics.get(name)
    holder = None if document is None else document.relative_to(design).as_posix()
    page = "/".join(parts[1:])
    if holder is None or (page and parts[0] != name):
        return None
    if not page and parts[0] == name and holder.endswith(f"/{K_README}"):
        return holder.removesuffix(f"/{K_README}")
    if page in ("", K_README):
        return holder
    if not holder.endswith(f"/{K_README}"):
        return None
    moved = f"{holder.removesuffix(K_README)}{page}"
    return moved if (design / moved).exists() else None


def _former_folder(path: Path, design: Path) -> Path | None:
    """Returns the folder a design page sat in before it moved into or out of _REVISION."""
    try:
        below = path.parent.resolve().relative_to(design.resolve())
    except ValueError:
        return None
    if not below.parts:
        return None
    if below.parts[0] == K_REVISION_FOLDER:
        return design.joinpath(*below.parts[1:])
    return design.joinpath(K_REVISION_FOLDER, *below.parts)


def _line_changes(path: Path, old: str, new: str) -> list[Rewrite]:
    """Returns one Rewrite per line that differs between two texts of the same line count."""
    old_lines, new_lines = old.splitlines(), new.splitlines()
    return [
        Rewrite(path, number, before, after)
        for number, (before, after) in enumerate(zip(old_lines, new_lines), start=1)
        if before != after
    ]


def _read(path: Path) -> str | None:
    """Returns the text of a file, or None when it is not UTF-8."""
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None


def _drop_ignored(root: Path, paths: list[Path]) -> list[Path]:
    """Returns the paths git does not ignore below *root*; all of them outside a repository."""
    if not paths:
        return paths
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "check-ignore", "-z", "--stdin"],
            input="\0".join(str(path.resolve()) for path in paths) + "\0",
            capture_output=True, text=True, encoding="utf-8",
        )
    except OSError:
        return paths
    if completed.returncode not in (K_EXIT_SOME_IGNORED, K_EXIT_NONE_IGNORED):
        return paths
    ignored = {Path(entry).resolve() for entry in completed.stdout.split("\0") if entry}
    return [path for path in paths if path.resolve() not in ignored]
