"""The profile is what keeps the shared machinery from naming a module."""

from sushicore.profile import ModuleProfile


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
