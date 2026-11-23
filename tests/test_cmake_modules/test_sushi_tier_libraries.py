# test_sushi_tier_libraries.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.
"""How the tier functions resolve the links of a real two-tier configure, read from build.ninja."""

import re
import sys

import pytest

#: A static archive of the module named by the group, on any platform.
K_ARCHIVE = r"(?:lib)?{}\.(?:a|lib)\b"

#: The shared or import library of the tier library named by the group, on any platform.
K_TIER_LIBRARY = r"(?:lib)?{}\.(?:so|lib|dll\.a)\b"


def archive(module: str) -> str:
    """Return the pattern of the archive of *module*."""
    return K_ARCHIVE.format(re.escape(module))


def tier_library(name: str) -> str:
    """Return the pattern of the tier library whose output name is *name*."""
    return K_TIER_LIBRARY.format(re.escape(name))


@pytest.mark.medium
def test_tier_libraries_declared_once_configure(tiers_tree):
    assert tiers_tree.code == 0, tiers_tree.output


@pytest.mark.medium
def test_tier_libraries_declared_twice_stop_the_configure(configure):
    configured = configure("tiers", "-DTIERS_DECLARE_TWICE=ON")
    assert configured.code != 0
    assert configured.says("the tiers of 'demo' are already declared"), configured.output


@pytest.mark.medium
def test_tier_link_to_a_lower_tier_module_links_that_tiers_library(tiers_tree):
    block = tiers_tree.link_block("demo_high")
    assert re.search(tier_library("demo_low"), block)
    assert not re.search(archive("low_mod"), block)


@pytest.mark.medium
def test_tier_link_within_a_tier_hands_the_headers_and_no_archive(tiers_tree):
    assert "high_headers" in tiers_tree.compile_command("high_peer.cpp")
    block = tiers_tree.link_block("plain")
    assert re.search(archive("high_peer"), block)
    assert not re.search(archive("high_mod"), block)


@pytest.mark.medium
def test_tier_link_to_a_higher_tier_module_stops_the_configure(configure):
    configured = configure("tiers", "-DTIERS_LINK_UPWARDS=ON")
    assert configured.code != 0
    refusal = "the low module low_mod links high_mod, a module of the higher tier high"
    assert configured.says(refusal), configured.output


@pytest.mark.medium
def test_tier_module_linked_before_it_was_declared_stops_the_configure(configure):
    configured = configure("tiers", "-DTIERS_LINK_EARLY=ON")
    assert configured.code != 0
    refusal = "'early' linked high_mod before it was declared"
    assert configured.says(refusal), configured.output


@pytest.mark.medium
@pytest.mark.parametrize("module", ["high_peer", "high_mod", "low_mod"])
def test_tier_archives_link_each_module_archive_of_the_chain(tiers_tree, module):
    assert re.search(archive(module), tiers_tree.link_block("marked"))


@pytest.mark.medium
@pytest.mark.parametrize("tier", ["demo_high", "demo_low"])
def test_tier_archives_link_no_tier_library(tiers_tree, tier):
    assert not re.search(tier_library(tier), tiers_tree.link_block("marked"))


@pytest.mark.medium
@pytest.mark.skipif(sys.platform != "win32", reason="the archives load whole on Windows only")
@pytest.mark.parametrize("module", ["high_peer", "high_mod", "low_mod"])
def test_tier_archives_load_each_static_module_whole_on_windows(tiers_tree, module):
    whole = r"/WHOLEARCHIVE:\S*?" + archive(module)
    assert re.search(whole, tiers_tree.link_block("marked"), re.IGNORECASE)


@pytest.mark.medium
@pytest.mark.skipif(sys.platform == "win32", reason="off Windows no archive loads whole")
def test_tier_archives_add_no_whole_archive_option_off_windows(tiers_tree):
    assert not re.search(r"whole-?archive", tiers_tree.link_block("marked"), re.IGNORECASE)


@pytest.mark.medium
def test_tier_link_of_an_unmarked_program_names_the_tier_library(tiers_tree):
    block = tiers_tree.link_block("shipped")
    assert re.search(tier_library("demo_high"), block)
    assert not re.search(archive("high_peer"), block)
