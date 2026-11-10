# shard_registrations.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Reads the shard registrations of a build tree out of its CTest test files."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ..files import Files
from .shards import test_file_texts

#: An ``add_test`` call of a generated CTest test file: the test's name and its quoted command line.
_K_ADD_TEST = re.compile(r'^[ 	]*add_test\(\[=\[(?P<name>[^\]]+)\]=\]\s+(?P<command>.*)\)\s*$', re.MULTILINE)

#: A ``set_tests_properties`` call of a generated CTest test file: the test's name and its properties.
_K_PROPERTIES = re.compile(r'^[ 	]*set_tests_properties\(\[=\[(?P<name>[^\]]+)\]=\]\s+PROPERTIES\s+(?P<properties>.*)\)\s*$',
                           re.MULTILINE)

#: One quoted word of a command line or one ``KEY "value"`` property.
_K_QUOTED = re.compile(r'"((?:[^"\\]|\\.)*)"')
_K_PROPERTY = re.compile(r'(?P<key>[A-Z_]+)\s+"(?P<value>(?:[^"\\]|\\.)*)"')

_K_FILTER = "--gtest_filter="
_K_OUTPUT = "--gtest_output="


@dataclass(frozen=True, slots=True)
class ShardRegistration:
    """One CTest test that runs a share of a GoogleTest program's cases.

    Attributes:
        name: The CTest name, ``<program>.<size>_shard_<index>of<count>``.
        program: The test program the name carries.
        size_filter: The GoogleTest filter the shard registers for its size.
        arguments: The registered arguments other than the filter and the XML output.
        environment: The shard variables, ``GTEST_TOTAL_SHARDS`` and ``GTEST_SHARD_INDEX``.
        labels: The CTest labels, the size and possibly ``quarantined``.
        timeout: The CTest timeout in seconds, or None when the shard has none.
        needs_accelerator: Whether the shard declares ``RESOURCE_GROUPS``, which it does when it runs on a
            real accelerator, so that no two such shards run at once on one.
    """

    name: str
    program: str
    size_filter: str
    arguments: tuple[str, ...]
    environment: dict[str, str]
    labels: tuple[str, ...]
    timeout: float | None
    needs_accelerator: bool = False


def shard_registrations(tree: Path, files: Files) -> list[ShardRegistration]:
    """Return the shard registrations of the build tree *tree*, in the order its test files name them.

    A shard is a registered test that carries a ``--gtest_filter`` and ``GTEST_TOTAL_SHARDS``.
    """
    registered: list[ShardRegistration] = []
    seen: set[str] = set()
    for text in test_file_texts(tree, files):
        properties = {found.group("name"): _properties(found.group("properties"))
                      for found in _K_PROPERTIES.finditer(text)}
        for found in _K_ADD_TEST.finditer(text):
            shard = _shard(found.group("name"), _K_QUOTED.findall(found.group("command")),
                           properties.get(found.group("name"), {}))
            if shard is not None and shard.name not in seen:
                seen.add(shard.name)
                registered.append(shard)
    return registered


def _properties(text: str) -> dict[str, str]:
    """Return the ``KEY "value"`` properties of a ``set_tests_properties`` call."""
    return {found.group("key"): found.group("value") for found in _K_PROPERTY.finditer(text)}


def _shard(name: str, command: list[str], properties: dict[str, str]) -> ShardRegistration | None:
    """Return the registration of *name* when it is a shard, or None."""
    environment = dict(item.partition("=")[::2] for item in properties.get("ENVIRONMENT", "").split(";") if item)
    filters = [word[len(_K_FILTER):] for word in command[1:] if word.startswith(_K_FILTER)]
    if "GTEST_TOTAL_SHARDS" not in environment or not filters or "." not in name:
        return None
    timeout = properties.get("TIMEOUT")
    return ShardRegistration(
        name=name, program=name.rpartition(".")[0], size_filter=filters[0],
        arguments=tuple(word for word in command[1:] if not word.startswith((_K_FILTER, _K_OUTPUT))),
        environment=environment, labels=tuple(label for label in properties.get("LABELS", "").split(";") if label),
        timeout=float(timeout) if timeout else None, needs_accelerator=bool(properties.get("RESOURCE_GROUPS")))
