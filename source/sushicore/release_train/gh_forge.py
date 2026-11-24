# gh_forge.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Waits for the workflows of a commit on GitHub, through the gh command."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import final

from ..proc import CommandRunner

#: Seconds between two looks at a workflow, so a long wait spends little of the API limit.
K_POLL_SECONDS = 60.0
#: Looks before a workflow that never starts or never ends counts as failed.
K_MAX_POLLS = 180


@final
class GhForge:
    """Polls the runs of one workflow of a commit until the newest one has finished."""

    def __init__(self, runner: CommandRunner, sleep: Callable[[float], None]) -> None:
        self._runner = runner
        self._sleep = sleep

    def ci_passed(self, repo: Path, commit: str) -> bool:
        return self._passed(repo, commit, "ci.yml")

    def release_passed(self, repo: Path, commit: str) -> bool:
        return self._passed(repo, commit, "release.yml")

    def _passed(self, repo: Path, commit: str, workflow: str) -> bool:
        command = ["gh", "run", "list", "--commit", commit, "--workflow", workflow, "--limit", "1",
                   "--json", "status,conclusion"]
        for _ in range(K_MAX_POLLS):
            code, out, _err = self._runner.capture(command, cwd=repo)
            runs = json.loads(out) if code == 0 and out.strip() else []
            if runs and runs[0].get("status") == "completed":
                return runs[0].get("conclusion") == "success"
            self._sleep(K_POLL_SECONDS)
        return False
