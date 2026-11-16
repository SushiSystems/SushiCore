# pre_move_digest_writer.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Writes, once, the frozen digest file of the shared files as SushiSkills held them before the move."""

from __future__ import annotations

import sys
import tempfile
from collections.abc import Callable, Iterable
from pathlib import Path

from .git_reader import GitReader
from .header_merger import HeaderMerger
from .licence_toolkit import load_toolkit
from .pre_move_digests import K_DIGESTS_PATH, K_FORMAT_VERSION, body_digest
from .sync_service import K_COMMUNITY, K_EXCLUDED, K_TOOLS

K_CORE_REVISION = "HEAD"
BodyOf = Callable[[str, str], str]


def collect_digests(skills: GitReader, paths: Iterable[str], body_of: BodyOf) -> dict[str, list[str]]:
    """Returns, for each path, the sorted digests of every version SushiSkills ever committed.

    Args:
        skills: The SushiSkills clone, read through git.
        paths: The shared paths to look up.
        body_of: Returns the body the sync compares, from a path and a text.
    """
    found = {}
    for path in sorted(paths):
        texts = (skills.show(revision, path) for revision in skills.revisions(path))
        digests = {body_digest(body_of(path, text)) for text in texts if text is not None}
        if digests:
            found[path] = sorted(digests)
    return found


def render(digests: dict[str, list[str]]) -> str:
    """Returns the TOML text of the digest file, one table per path, in path order."""
    lines = [
        "# SHA-256 of the body of each shared file as SushiSkills held it before the move to SushiCore.",
        "# Written once by pre_move_digest_writer.py; never edited by hand.",
        f"format_version = {K_FORMAT_VERSION}",
    ]
    for path in sorted(digests):
        rows = "".join(f'    "{digest}",\n' for digest in sorted(digests[path]))
        lines += ["", f'[files."{path}"]', f"digests = [\n{rows}]"]
    return "\n".join([*lines, ""])


def write_digests(skills_clone: Path, core_clone: Path, target: Path = K_DIGESTS_PATH) -> int:
    """Writes the digest file from the two clones and returns the number of digests written."""
    core = GitReader(core_clone)
    shared = [path for path in core.files(K_CORE_REVISION, K_TOOLS, *K_COMMUNITY) if path not in K_EXCLUDED]
    with load_toolkit(core, K_CORE_REVISION) as toolkit, tempfile.TemporaryDirectory() as scratch:
        merger = HeaderMerger(toolkit, Path(scratch))
        digests = collect_digests(GitReader(skills_clone), shared, merger.body)
    target.write_text(render(digests), encoding="utf-8", newline="\n")
    return sum(len(rows) for rows in digests.values())


def main(arguments: list[str]) -> int:
    """Runs the writer as `python -m ... <skills clone> <core clone>`."""
    if len(arguments) != 2:
        sys.stderr.write("usage: pre_move_digest_writer <SushiSkills clone> <SushiCore clone>\n")
        return 2
    sys.stdout.write(f"{write_digests(Path(arguments[0]), Path(arguments[1]))} digests written\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
