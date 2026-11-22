# SushiPrecompiledHeaders.cmake
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.

# The standard headers substantially every translation unit of a Sushi C++ target parses, and the
# one function that precompiles them for a target. SushiEngine measured the set: the common headers
# made 66% to 90% of the preprocessed lines of a unit across three targets. The set is standard
# headers only. A repository's own headers are cheap to parse and edited often, and a header in a
# precompiled header rebuilds every unit of the target when it changes.

include_guard(GLOBAL)

# sushi_precompile_headers(<target> [EXTRA <header>...] [SKIP <source>...])
#   Gives <target> the common header set plus the EXTRA headers its own translation units
#   substantially all include, such as <vulkan/vulkan.h> for a renderer. The common set is not
#   edited to suit one caller; EXTRA is where a target's own set goes.
#
#   SKIP names sources that must not take the precompiled header. A precompiled header serves only
#   a unit compiled with the flags it was built with, so a source with flags of its own, -fsycl
#   above all, fails with it. Pass the list that selects those flags, so the two cannot drift.
#
#   A header-only target compiles nothing, so it is refused: its consumers pay for its headers.
function(sushi_precompile_headers target)
    cmake_parse_arguments(ARG "" "" "EXTRA;SKIP" ${ARGN})
    if(ARG_UNPARSED_ARGUMENTS)
        message(FATAL_ERROR
            "sushi_precompile_headers(${target}): unexpected argument(s) '${ARG_UNPARSED_ARGUMENTS}'.")
    endif()
    if(NOT TARGET ${target})
        message(FATAL_ERROR "sushi_precompile_headers(${target}): no target of that name exists.")
    endif()
    get_target_property(type ${target} TYPE)
    if(type STREQUAL "INTERFACE_LIBRARY")
        message(FATAL_ERROR
            "sushi_precompile_headers(${target}): the target is header-only, so it has no "
            "translation units of its own to precompile for. Give the precompiled header to the "
            "targets that include its headers.")
    endif()

    set(common
        <algorithm> <array> <atomic> <cmath> <cstddef> <cstdint> <cstdio> <cstring>
        <functional> <limits> <map> <memory> <optional> <set> <sstream> <string>
        <type_traits> <unordered_map> <utility> <variant> <vector>)
    target_precompile_headers(${target} PRIVATE ${common} ${ARG_EXTRA})

    if(ARG_SKIP)
        set_source_files_properties(${ARG_SKIP}
            TARGET_DIRECTORY ${target}
            PROPERTIES SKIP_PRECOMPILE_HEADERS ON)
    endif()
endfunction()
