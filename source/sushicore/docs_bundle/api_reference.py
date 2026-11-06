# api_reference.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Builds a repository's API reference and stages the Doxygen XML a bundle carries."""

from __future__ import annotations

import shutil
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, final
from xml.etree import ElementTree

from ..files import DiskFiles, Files
from .errors import ApiReferenceError

K_INDEX = "index.xml"


@dataclass(frozen=True, slots=True)
class ApiSource:
    """Holds how a repository builds its API reference and where the XML lands."""

    build: Callable[[], int]
    xml_dir: Path


@final
class RecordingApiBuild:
    """An API build that counts its calls, returns a set exit code and writes the XML given."""

    def __init__(
        self,
        code: int = 0,
        *,
        written: Mapping[Path, str] | None = None,
        files: Files | None = None,
    ) -> None:
        """Stores the exit code to return and the files to write on each call.

        Args:
            code: The exit code every call returns.
            written: The text to write, by path, on each call.
            files: The file system the text is written through; the disk when None.
        """
        self.code = code
        self.calls = 0
        self._written = dict(written or {})
        self._files: Files = files if files is not None else DiskFiles()

    def __call__(self) -> int:
        """Counts the call, writes the files it was given and returns the exit code."""
        self.calls += 1
        for path, text in self._written.items():
            self._files.write_text(path, text)
        return self.code


def _named_files(index: Path, text: str) -> list[str]:
    """Returns the index and the file of every compound the index *text* names."""
    try:
        root = ElementTree.fromstring(text)
    except ElementTree.ParseError as error:
        raise ApiReferenceError(f"{index} is not valid XML: {error}") from error
    refids = sorted({compound.get("refid", "") for compound in root.iter("compound")})
    return [K_INDEX, *(f"{refid}.xml" for refid in refids if refid)]


def stage_api(
    source: ApiSource | None, destination: Path, *, files: Files | None = None,
) -> None:
    """Builds the API reference and copies the XML its index names into *destination*.

    Args:
        source: How the repository builds its API reference; None when it builds none.
        destination: The folder the XML is copied into.
        files: The file system the index and the files it names are looked up in; the disk
            when None. The copy itself always reads and writes the disk.

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
    files = files if files is not None else DiskFiles()
    index = source.xml_dir / K_INDEX
    if not files.is_file(index):
        raise ApiReferenceError(
            f"{index} does not exist; set GENERATE_XML = YES in the Doxyfile."
        )
    names = _named_files(index, files.read_text(index))
    for name in names:
        if not files.is_file(source.xml_dir / name):
            raise ApiReferenceError(f"{index} names {name}, which is missing.")
    destination.mkdir(parents=True, exist_ok=True)
    for name in names:
        shutil.copyfile(source.xml_dir / name, destination / name)
