# __init__.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""The design topics: one topic per subject, each module owned by one topic."""

from __future__ import annotations

from .check import Finding, check_design
from .commands import register_design_commands
from .errors import DesignError, OwnedModuleError, TopicNotFoundError
from .merge import MergeResult, Overlap, TopicMerger, find_overlap
from .model import Phase, TopicDocument, parse_topic
from .store import DesignStore, Topic

__all__ = [
    "DesignError",
    "DesignStore",
    "Finding",
    "MergeResult",
    "Overlap",
    "OwnedModuleError",
    "Phase",
    "Topic",
    "TopicDocument",
    "TopicMerger",
    "TopicNotFoundError",
    "check_design",
    "find_overlap",
    "parse_topic",
    "register_design_commands",
]
