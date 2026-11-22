# verbs.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Names the canonical verbs every Sushi CLI spells alike."""

from __future__ import annotations

from ..command_groups import K_BACKLOG, K_DESIGN

K_SETUP = "setup"
K_DOCTOR = "doctor"
K_LINK = "link"
K_UNLINK = "unlink"
K_BUILD = "build"
K_TEST = "test"
K_RUN = "run"
K_BENCH = "bench"
K_CHECK = "check"
K_CLEAN = "clean"
K_PACKAGE = "package"
K_DOCS = "docs"
K_CONFIG = "config"
K_ENV = "env"
K_WHERE = "where"
K_STATUS = "status"

#: Every canonical verb; a CLI registers each one that applies to its repository.
K_CANONICAL_VERBS = (
    K_SETUP, K_DOCTOR, K_LINK, K_UNLINK, K_BUILD, K_TEST, K_RUN, K_BENCH, K_CHECK, K_CLEAN,
    K_PACKAGE, K_DOCS, K_CONFIG, K_ENV, K_WHERE, K_STATUS, K_BACKLOG, K_DESIGN,
)
