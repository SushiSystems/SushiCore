"""The profile is what keeps the shared machinery from naming a module."""

from sushicore.profile import RELEASE_MANIFEST, ModuleProfile


def test_env_overrides_are_prefixed_from_the_profile():
    profile = ModuleProfile(name="SushiBLAS", program="sb", env_prefix="SB")
    overrides = profile.env_overrides()
    assert overrides["cxx"] == "SB_CXX"
    assert overrides["vcpkg_root"] == "SB_VCPKG_ROOT"


def test_extra_env_overrides_win_over_the_prefix():
    """A collision is the only thing that proves precedence, so use one."""
    plain = ModuleProfile(name="SushiBLAS", program="sb", env_prefix="SB")
    assert plain.env_overrides()["cxx"] == "SB_CXX"

    overridden = ModuleProfile(
        name="SushiBLAS", program="sb", env_prefix="SB",
        extra_env_overrides={"cxx": "SUSHIRUNTIME_CXX"})
    assert overridden.env_overrides()["cxx"] == "SUSHIRUNTIME_CXX"


def test_an_extra_override_for_a_non_tool_field_is_still_carried():
    """The real use: a sibling directory, which has no prefix-derived entry."""
    profile = ModuleProfile(
        name="SushiBLAS", program="sb", env_prefix="SB",
        siblings=("sushiruntime",),
        extra_env_overrides={"sushiruntime_dir": "SUSHIRUNTIME_DIR"})
    assert profile.env_overrides()["sushiruntime_dir"] == "SUSHIRUNTIME_DIR"


def test_sibling_skip_dirs_names_every_sibling():
    profile = ModuleProfile(name="SushiAI", program="sa", env_prefix="SA",
                            siblings=("sushiruntime", "sushiblas"))
    assert set(profile.sibling_skip_dirs()) == {"sushiruntime", "sushiblas"}


def test_markers_name_the_root_marker_then_the_release_manifest():
    profile = ModuleProfile(name="SushiEngine", program="se", env_prefix="SE",
                            root_marker=".sushiengine-root")
    assert profile.markers() == (".sushiengine-root", RELEASE_MANIFEST)


def test_presence_is_binary_when_the_release_manifest_is_there(tmp_path):
    profile = ModuleProfile(name="SushiEngine", program="se", env_prefix="SE")
    (tmp_path / RELEASE_MANIFEST).write_text('{"product": "sushiengine"}')
    assert profile.presence(tmp_path) == "binary"


def test_presence_is_source_without_the_release_manifest(tmp_path):
    profile = ModuleProfile(name="SushiEngine", program="se", env_prefix="SE")
    (tmp_path / "CMakeLists.txt").write_text("")
    assert profile.presence(tmp_path) == "source"


def test_a_directory_named_like_the_manifest_is_not_a_binary_install(tmp_path):
    """Only a file counts; a stray directory of that name must not fool the walk."""
    profile = ModuleProfile(name="SushiEngine", program="se", env_prefix="SE")
    (tmp_path / RELEASE_MANIFEST).mkdir()
    assert profile.presence(tmp_path) == "source"


def test_not_a_project_message_names_both_markers():
    profile = ModuleProfile(name="SushiEngine", program="se", env_prefix="SE",
                            root_marker=".sushiengine-root")
    message = profile.not_a_project_message()
    assert ".sushiengine-root" in message
    assert RELEASE_MANIFEST in message
