# budget.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Decides the scope of a test run, runs the budget reader a repository carries and gates the run on it."""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Optional

from ..files import DiskFiles, Files
from .labels import K_DEFAULT_LABELS, LabelSelection
from .module_tests import ModuleTests
from .result_files import ResultFileError, case_names
from .shards import program_of
from .slow_rerun import SlowTestRerun

#: Where the shared budget reader sits below a repository root.
K_READER = Path("tools") / "testing" / "test_budget.py"

#: Where a repository lists the tests that already break a limit, below its root.
K_EXEMPTIONS = Path("tests") / "budget_exemptions.toml"

#: What the command says when the reader could not judge a run, such as a reader older than the command.
K_UNUSABLE_TEXT = "The budget reader could not judge the run; copy the shared tools into the repository."


def scope_of(selection: LabelSelection, *, filtered: bool, every_size: bool, repeated: bool) -> str:
    """Returns the scope the budget reader judges a run by.

    ``default`` is the run of ``small`` and ``medium`` that nothing narrowed, ``large`` is a run of every
    size, and ``partial`` is any other, whose totals never gate.

    Args:
        selection: The labels the run selected.
        filtered: Whether a name filter narrowed the run.
        every_size: Whether the run was asked for every size.
        repeated: Whether the run repeated its tests.
    """
    if filtered or repeated:
        return "partial"
    if every_size:
        return "large"
    if selection.sizes == K_DEFAULT_LABELS and not selection.quarantined:
        return "default"
    return "partial"


def reader_command(root: Path, junit: Path, scope: str, wall_seconds: float,
                   rebuilt: bool = True, *, files: Files | None = None,
                   cases: Path | None = None, reruns: Sequence[Path] = (),
                   programs: Path | None = None, gate: bool = False,
                   list_over: Path | None = None) -> Optional[list[str]]:
    """Returns the command that judges a run, or None when the root carries no reader.

    Args:
        root: The repository root.
        junit: The JUnit file the run wrote.
        scope: What :func:`scope_of` returned.
        wall_seconds: The wall time of the whole run.
        rebuilt: Whether the tree was current when the run began; a run that was not is marked
            "(not rebuilt)" and never gates.
        files: The file system the reader and the exemption file are looked for in; the disk when None.
        cases: The folder of the GoogleTest XML files the shards wrote; the reader adds their per-case times.
        reruns: The JUnit files, or folders of GoogleTest XML files, of tests run again alone.
        programs: The JSON file from suite name to test program.
        gate: Makes the reader exit 1 on a finding.
        list_over: Makes the reader write the tests over a limit to this file and print nothing.
    """
    files = files if files is not None else DiskFiles()
    reader = root / K_READER
    if not files.is_file(reader):
        return None
    command = [sys.executable, str(reader), str(junit), "--scope", scope,
               "--wall", f"{wall_seconds:.1f}", "--root", str(root)]
    if not rebuilt:
        command.append("--not-rebuilt")
    if cases is not None:
        command += ["--cases", str(cases)]
    for rerun in reruns:
        command += ["--rerun", str(rerun)]
    if programs is not None:
        command += ["--programs", str(programs)]
    if files.is_file(root / K_EXEMPTIONS):
        command += ["--exemptions", str(root / K_EXEMPTIONS)]
    if gate:
        command.append("--gate")
    if list_over is not None:
        command += ["--list-over", str(list_over)]
    return command


def program_map(cases: Path, files: Files) -> dict[str, str]:
    """Return the test program of each suite whose cases the shards of a run wrote into *cases*.

    Each ``/`` part of a case's suite is a key, so a parametrised ``Prefix/Suite`` names its program by
    ``Suite`` too, the part the reader looks up.
    """
    programs: dict[str, str] = {}
    for path in files.children(cases):
        program = program_of(path.stem)
        if path.suffix != ".xml" or program is None:
            continue
        try:
            names = case_names(files.read_text(path))
        except ResultFileError:
            continue
        for name in names:
            for part in name.split(".")[0].split("/"):
                programs[part] = program
    return programs


def judge_run(module: ModuleTests, tree: Path, junit: Path, scope: str, wall_seconds: float,
              rebuilt: bool = True, *, files: Files | None = None,
              cases: Path | None = None, rerun: Path | None = None) -> int:
    """Print the budget line of a run and return 1 when the run breaks a time limit, 0 otherwise.

    The reader first lists the tests over a limit; they run again alone, one at a time, and the reader
    then judges each by its time alone, so the load of the parallel run does not fail it. A tree that
    was not current never gates. Nothing is judged when the repository carries no reader or the run
    wrote no JUnit file, and a reader that cannot judge the run, such as one older than this command,
    fails it with the reader's exit code.

    Args:
        module: What the module CLI hands the command.
        tree: The built tree the run tested.
        junit: The JUnit file the run wrote.
        scope: What :func:`scope_of` returned.
        wall_seconds: The wall time of the whole run.
        rebuilt: Whether the tree was current when the run began.
        files: The file system the reader, the result files and the exemption file are looked for in;
            the disk when None.
        cases: The folder of the GoogleTest XML files the shards wrote, used when it exists.
        rerun: The results of the failed tests rerun alone, which the reader also takes as times alone.
    """
    files = files if files is not None else DiskFiles()
    root = module.project_root()
    console = module.console()
    if reader_command(root, junit, scope, wall_seconds, files=files) is None:
        return 0
    if not files.is_file(junit):
        console.warn("The run wrote no JUnit file, so the budget line is skipped.")
        return 0
    present = cases if cases is not None and files.is_dir(cases) else None
    programs = None
    if present is not None:
        programs = tree / "Testing" / "programs.json"
        files.write_text(programs, json.dumps(program_map(present, files), indent=2, sort_keys=True) + "\n")
    over_file = tree / "Testing" / "over_limit.txt"
    files.remove(over_file)
    failed_alone = (rerun,) if rerun is not None else ()
    listing = reader_command(root, junit, scope, wall_seconds, rebuilt, files=files, cases=present,
                             programs=programs, reruns=failed_alone, list_over=over_file)
    code = module.run(listing, root)
    if code != 0:
        console.error(K_UNUSABLE_TEXT)
        return code
    over = [line for line in files.read_text(over_file).splitlines() if line] if files.is_file(over_file) else []
    reruns = failed_alone + SlowTestRerun(module, tree, files).rerun(over)
    command = reader_command(root, junit, scope, wall_seconds, rebuilt, files=files, cases=present,
                             programs=programs, reruns=reruns, gate=True)
    code = module.run(command, root)
    if code == 1:
        console.error("The run broke a time limit.")
    elif code != 0:
        console.error(K_UNUSABLE_TEXT)
    return code
