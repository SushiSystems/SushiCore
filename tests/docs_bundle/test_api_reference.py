# test_api_reference.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""Tests the staging of Doxygen's XML: what is built, what is copied, what stops it."""

from __future__ import annotations

from pathlib import Path

import pytest

from sushicore.docs_bundle.api_reference import ApiSource, RecordingApiBuild, stage_api
from sushicore.docs_bundle.errors import ApiReferenceError
from sushicore.files_memory import MemoryFiles

K_XML = Path("xml")
K_OUT = Path("out")

K_INDEX = (
    '<?xml version="1.0"?>\n<doxygenindex>\n'
    '  <compound refid="classsr_1_1Graph" kind="class"><name>sr::Graph</name></compound>\n'
    '  <compound refid="namespacesr" kind="namespace"><name>sr</name></compound>\n'
    "</doxygenindex>\n"
)


def _source(build: RecordingApiBuild) -> ApiSource:
    """Returns an API source that builds with *build* and keeps its XML in `xml`."""
    return ApiSource(build=build, xml_dir=K_XML)


@pytest.mark.medium
def test_stage_builds_then_copies_what_the_index_names(tmp_path):
    """Runs the build once and copies the index and the files it names, nothing stale."""
    xml_dir = tmp_path / "xml"
    written = {xml_dir / "index.xml": K_INDEX}
    written.update({
        xml_dir / name: "<doxygen/>\n"
        for name in ("classsr_1_1Graph.xml", "namespacesr.xml", "classsr_1_1Removed.xml")
    })
    build = RecordingApiBuild(written=written)
    destination = tmp_path / "staging" / "api" / "xml"
    stage_api(ApiSource(build=build, xml_dir=xml_dir), destination)
    assert build.calls == 1
    assert sorted(path.name for path in destination.iterdir()) == [
        "classsr_1_1Graph.xml",
        "index.xml",
        "namespacesr.xml",
    ]


@pytest.mark.small
def test_stage_refuses_a_repository_with_no_api_source():
    """Stops when the publish list asks for an API the command cannot build."""
    with pytest.raises(ApiReferenceError) as caught:
        stage_api(None, K_OUT)
    assert "api = true" in str(caught.value)


@pytest.mark.small
def test_stage_reports_a_failed_build():
    """Carries the exit code of a build that failed."""
    with pytest.raises(ApiReferenceError) as caught:
        stage_api(_source(RecordingApiBuild(code=3)), K_OUT, files=MemoryFiles())
    assert str(caught.value) == "The API reference build exited with code 3."


@pytest.mark.small
def test_stage_reports_a_build_that_wrote_no_xml():
    """Points at GENERATE_XML when the build left no index."""
    with pytest.raises(ApiReferenceError) as caught:
        stage_api(_source(RecordingApiBuild()), K_OUT, files=MemoryFiles())
    assert str(caught.value) == (
        f"{K_XML / 'index.xml'} does not exist; set GENERATE_XML = YES in the Doxyfile."
    )


@pytest.mark.small
def test_stage_reports_an_index_that_names_a_missing_file():
    """Names the file the index lists and the folder lacks."""
    files = MemoryFiles({
        K_XML / "index.xml": K_INDEX,
        K_XML / "classsr_1_1Graph.xml": "<doxygen/>\n",
    })
    with pytest.raises(ApiReferenceError) as caught:
        stage_api(_source(RecordingApiBuild()), K_OUT, files=files)
    assert str(caught.value) == f"{K_XML / 'index.xml'} names namespacesr.xml, which is missing."


@pytest.mark.small
def test_stage_reports_an_index_that_is_not_xml():
    """Reports a malformed index as its own failure, not as a parser traceback."""
    files = MemoryFiles({K_XML / "index.xml": "<doxygenindex>"})
    with pytest.raises(ApiReferenceError) as caught:
        stage_api(_source(RecordingApiBuild()), K_OUT, files=files)
    assert str(caught.value).startswith(f"{K_XML / 'index.xml'} is not valid XML: ")
