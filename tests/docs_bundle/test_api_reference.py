# test_api_reference.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests the staging of Doxygen's XML: what is built, what is copied, what stops it."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.docs_bundle.api_reference import ApiSource, stage_api
from sushicore.docs_bundle.errors import ApiReferenceError

K_INDEX = (
    '<?xml version="1.0"?>\n<doxygenindex>\n'
    '  <compound refid="classsr_1_1Graph" kind="class"><name>sr::Graph</name></compound>\n'
    '  <compound refid="namespacesr" kind="namespace"><name>sr</name></compound>\n'
    "</doxygenindex>\n"
)


def _xml_dir(tmp_path: Path) -> Path:
    """Writes an XML output folder with two named compounds and one stale file."""
    folder = tmp_path / "xml"
    folder.mkdir()
    (folder / "index.xml").write_text(K_INDEX, encoding="utf-8")
    for name in ("classsr_1_1Graph.xml", "namespacesr.xml", "classsr_1_1Removed.xml"):
        (folder / name).write_text("<doxygen/>\n", encoding="utf-8")
    return folder


def test_stage_builds_then_copies_what_the_index_names(tmp_path):
    """Runs the build once and copies the index and the files it names, nothing stale."""
    calls: list[str] = []
    source = ApiSource(build=lambda: calls.append("build") or 0, xml_dir=_xml_dir(tmp_path))
    destination = tmp_path / "staging" / "api" / "xml"
    stage_api(source, destination)
    assert calls == ["build"]
    assert sorted(path.name for path in destination.iterdir()) == [
        "classsr_1_1Graph.xml",
        "index.xml",
        "namespacesr.xml",
    ]


def test_stage_refuses_a_repository_with_no_api_source(tmp_path):
    """Stops when the publish list asks for an API the command cannot build."""
    with pytest.raises(ApiReferenceError) as caught:
        stage_api(None, tmp_path / "out")
    assert "api = true" in str(caught.value)


def test_stage_reports_a_failed_build(tmp_path):
    """Carries the exit code of a build that failed."""
    with pytest.raises(ApiReferenceError) as caught:
        stage_api(ApiSource(build=lambda: 3, xml_dir=_xml_dir(tmp_path)), tmp_path / "out")
    assert "3" in str(caught.value)


def test_stage_reports_a_build_that_wrote_no_xml(tmp_path):
    """Points at GENERATE_XML when the build left no index."""
    with pytest.raises(ApiReferenceError) as caught:
        stage_api(ApiSource(build=lambda: 0, xml_dir=tmp_path / "nothing"), tmp_path / "out")
    assert "GENERATE_XML" in str(caught.value)


def test_stage_reports_an_index_that_names_a_missing_file(tmp_path):
    """Names the file the index lists and the folder lacks."""
    folder = _xml_dir(tmp_path)
    (folder / "namespacesr.xml").unlink()
    with pytest.raises(ApiReferenceError) as caught:
        stage_api(ApiSource(build=lambda: 0, xml_dir=folder), tmp_path / "out")
    assert "namespacesr.xml" in str(caught.value)


def test_stage_reports_an_index_that_is_not_xml(tmp_path):
    """Reports a malformed index as its own failure, not as a parser traceback."""
    folder = _xml_dir(tmp_path)
    (folder / "index.xml").write_text("<doxygenindex>", encoding="utf-8")
    with pytest.raises(ApiReferenceError):
        stage_api(ApiSource(build=lambda: 0, xml_dir=folder), tmp_path / "out")
