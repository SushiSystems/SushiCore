# test_package_resolver.py
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under PolyForm Noncommercial 1.0.0. See LICENSE.
# Commercial use requires a licence from Sushi Systems.
"""Tests for the bottom-up resolution of a consumer's closure."""

from __future__ import annotations

import pytest

from sushicore.provision.sushi_packages.package_environment import K_MARKER
from sushicore.provision.sushi_packages.package_error import (
    PackageConflictError,
    PackageError,
)

from .package_fakes import FakeBuilder, Rig, make_library

pytestmark = pytest.mark.medium


@pytest.fixture
def rig(tmp_path):
    """Return a workspace and a resolver over a temporary store."""
    return Rig(tmp_path)


def _digest(package_set, name):
    """Return the digest of *name* in *package_set*."""
    return package_set.get(name).package.digest


def test_the_diamond_resolves_one_runtime_package(rig):
    """AI to BLAS to Runtime and AI to Runtime give one runtime package, built once."""
    result = rig.resolver.resolve(rig.request())
    assert result.names() == ["sushilog", "sushiruntime", "sushiblas"]
    built = [request.key.name for request in rig.builder.requests]
    assert built == ["sushilog", "sushiruntime", "sushiblas"]
    blas = rig.store.find_digest("sushiblas", _digest(result, "sushiblas"))
    assert dict(blas.below())["sushiruntime"] == _digest(result, "sushiruntime")


def test_a_changed_runtime_source_gives_blas_a_new_key(rig):
    """A changed runtime source gives the runtime and the BLAS a new digest, not the log."""
    before = rig.resolver.resolve(rig.request())
    (rig.workspace / "sushiruntime" / "src" / "a.cpp").write_text("// changed", encoding="utf-8")
    after = rig.resolver.resolve(rig.request())
    assert _digest(after, "sushiruntime") != _digest(before, "sushiruntime")
    assert _digest(after, "sushiblas") != _digest(before, "sushiblas")
    assert _digest(after, "sushilog") == _digest(before, "sushilog")


def test_a_docs_only_difference_gives_no_new_key(rig):
    """A change under docs/ and in a page leaves every digest and builds nothing."""
    before = rig.resolver.resolve(rig.request())
    runtime = rig.workspace / "sushiruntime"
    (runtime / "docs").mkdir()
    (runtime / "docs" / "guide.txt").write_text("text", encoding="utf-8")
    (runtime / "README.md").write_text("page", encoding="utf-8")
    builds = len(rig.builder.requests)
    after = rig.resolver.resolve(rig.request())
    digests = [[_digest(result, n) for n in result.names()] for result in (before, after)]
    assert digests[0] == digests[1]
    assert len(rig.builder.requests) == builds


def test_a_second_run_reuses_every_package_and_reports_it(rig):
    """The second resolution builds nothing and prints one reused line per library."""
    rig.resolver.resolve(rig.request())
    rig.lines.clear()
    rig.resolver.resolve(rig.request())
    assert [line.split(": ")[1].split(" ")[0] for line in rig.lines] == ["reused"] * 3
    assert len(rig.builder.requests) == 3


def test_the_first_run_reports_built_with_seconds(rig):
    """The first resolution prints one built line with a time per library."""
    rig.resolver.resolve(rig.request())
    assert all(": built " in line and line.endswith("s") for line in rig.lines)


def test_another_build_type_is_another_package(rig):
    """A package of another build type is never used for this one."""
    release = rig.resolver.resolve(rig.request())
    debug = rig.resolver.resolve(rig.request(build_type="Debug"))
    assert _digest(release, "sushilog") != _digest(debug, "sushilog")


def test_the_consumer_gets_its_own_stable_link(rig):
    """The definitions name the config folder through the consumer's link."""
    result = rig.resolver.resolve(rig.request())
    definitions = result.definitions()
    assert any(d.startswith("-DSushiRuntime_DIR=") and "@" in d and "sushiai" in d
               for d in definitions)
    assert len(definitions) == 3


def test_a_library_without_a_cli_and_without_a_package_is_refused(tmp_path):
    """The refusal names the fragment to add the cli key to."""
    rig = Rig(tmp_path)
    (rig.workspace / "sushilog" / "cli" / "sushistack.deps.toml").write_text(
        "[module]\ndepends_on = []\n", encoding="utf-8")
    with pytest.raises(PackageError, match="sushistack.deps.toml"):
        rig.resolver.resolve(rig.request())


def test_a_failed_build_leaves_no_partial_folder(tmp_path):
    """A build that raises leaves nothing staged behind."""
    rig = Rig(tmp_path, builder=FakeBuilder(fail=True))
    with pytest.raises(PackageError, match="build failed"):
        rig.resolver.resolve(rig.request())
    assert not list(rig.root.rglob("*.partial"))


def test_a_stale_forced_variable_is_ignored_with_a_warning(rig):
    """Without the nested marker a package variable chooses nothing."""
    first = rig.resolver.resolve(rig.request())
    rig.nested({"SUSHIBLAS_PACKAGE": str(first.get("sushiblas").package.prefix)})
    rig.resolver.resolve(rig.request())
    assert len(rig.warnings) == 1


def test_one_library_at_two_keys_is_refused_naming_both(rig):
    """A forced BLAS built against another runtime than the one chosen is a conflict."""
    first = rig.resolver.resolve(rig.request())
    old_runtime = _digest(first, "sushiruntime")
    (rig.workspace / "sushiruntime" / "src" / "a.cpp").write_text("// new", encoding="utf-8")
    rig.nested({K_MARKER: "1", "SUSHIBLAS_PACKAGE": str(first.get("sushiblas").package.prefix)})
    with pytest.raises(PackageConflictError) as caught:
        rig.resolver.resolve(rig.request())
    assert old_runtime[:12] in str(caught.value)
    assert "the source tree" in str(caught.value)


def test_a_forced_package_of_another_build_type_is_refused(rig):
    """A package handed down for another build type is refused."""
    first = rig.resolver.resolve(rig.request())
    rig.nested({K_MARKER: "1", "SUSHIBLAS_PACKAGE": str(first.get("sushiblas").package.prefix)})
    with pytest.raises(PackageError, match="build type"):
        rig.resolver.resolve(rig.request(build_type="Debug"))


def test_a_forced_package_is_taken_without_building(rig):
    """With the marker the handed-down BLAS is used, and nothing is built for it."""
    first = rig.resolver.resolve(rig.request())
    builds = len(rig.builder.requests)
    rig.nested({K_MARKER: "1", "SUSHIBLAS_PACKAGE": str(first.get("sushiblas").package.prefix)})
    second = rig.resolver.resolve(rig.request())
    assert _digest(second, "sushiblas") == _digest(first, "sushiblas")
    assert second.get("sushiblas").key is None
    assert len(rig.builder.requests) == builds


def test_a_cycle_is_refused(rig):
    """Libraries that depend on one another are refused naming the trail."""
    make_library(rig.workspace, "sushilog", ("sushiruntime",))
    with pytest.raises(PackageError, match="cycle"):
        rig.resolver.resolve(rig.request())


def test_a_filter_to_one_leaf_resolves_only_that_library(rig):
    """Naming the log builds the log alone and leaves the others out."""
    result = rig.resolver.resolve(rig.request(libraries=["sushilog"]))
    assert result.names() == ["sushilog"]
    assert result.left_out == ("sushiruntime", "sushiblas")
    assert [request.key.name for request in rig.builder.requests] == ["sushilog"]
    assert len(result.definitions()) == 1


def test_a_filter_to_a_library_with_a_dependency_resolves_both_in_order(rig):
    """Naming the runtime resolves the log below it first, and leaves the BLAS out."""
    result = rig.resolver.resolve(rig.request(libraries=["sushiruntime"]))
    assert result.names() == ["sushilog", "sushiruntime"]
    assert result.left_out == ("sushiblas",)


def test_a_filter_name_outside_the_closure_is_refused(rig):
    """The refusal names the library and the closure."""
    with pytest.raises(PackageError, match="sushifoo.*sushilog, sushiruntime, sushiblas"):
        rig.resolver.resolve(rig.request(libraries=["sushifoo"]))


def test_no_filter_equals_the_whole_closure(rig):
    """None and the full list of names give the same set."""
    whole = rig.resolver.resolve(rig.request())
    named = rig.resolver.resolve(rig.request(libraries=["sushiblas"]))
    assert named.names() == whole.names()
    assert [_digest(named, n) for n in named.names()] == [_digest(whole, n) for n in whole.names()]
    assert named.left_out == ()
    assert whole.left_out == ()


def test_the_key_of_a_library_is_the_same_with_and_without_the_filter(tmp_path):
    """A filtered resolution picks the package the whole one built."""
    rig = Rig(tmp_path)
    whole = rig.resolver.resolve(rig.request())
    filtered = rig.resolver.resolve(rig.request(libraries=["sushiruntime"]))
    for name in filtered.names():
        assert _digest(filtered, name) == _digest(whole, name)
        assert filtered.get(name).key == whole.get(name).key
    assert len(rig.builder.requests) == 3
