# api_reference.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Builds a repository's API reference and stages the Doxygen XML a bundle carries."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from xml.etree import ElementTree

from .errors import ApiReferenceError

K_INDEX = "index.xml"


@dataclass(frozen=True, slots=True)
class ApiSource:
    """Holds how a repository builds its API reference and where the XML lands."""

    build: Callable[[], int]
    xml_dir: Path


def _named_files(index: Path) -> list[str]:
    """Returns the index and the file of every compound it names."""
    try:
        root = ElementTree.parse(index).getroot()
    except ElementTree.ParseError as error:
        raise ApiReferenceError(f"{index} is not valid XML: {error}") from error
    refids = sorted({compound.get("refid", "") for compound in root.iter("compound")})
    return [K_INDEX, *(f"{refid}.xml" for refid in refids if refid)]


def stage_api(source: ApiSource | None, destination: Path) -> None:
    """Builds the API reference and copies the XML its index names into *destination*.

    Raises:
        ApiReferenceError: No source, a failed build, no XML, or a file the index names
            and the output folder lacks.
    """
    if source is None:
        raise ApiReferenceError(
            "docs/publish.toml sets api = true, and this command builds no API reference."
        )
    code = source.build()
    if code != 0:
        raise ApiReferenceError(f"The API reference build exited with code {code}.")
    index = source.xml_dir / K_INDEX
    if not index.is_file():
        raise ApiReferenceError(
            f"{index} does not exist; set GENERATE_XML = YES in the Doxyfile."
        )
    destination.mkdir(parents=True, exist_ok=True)
    for name in _named_files(index):
        path = source.xml_dir / name
        if not path.is_file():
            raise ApiReferenceError(f"{index} names {name}, which is missing.")
        shutil.copyfile(path, destination / name)
