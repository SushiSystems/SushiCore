# SushiAbiPinning.cmake
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.

# The C runtime and the STL layout every build type of a Sushi C++ tree compiles against, so a
# Debug tree links what a Release tree links. The Sushi libraries below a repository arrive as
# Release packages; a debug C runtime or a checked STL above them would put two heaps and two
# container layouts in one process. Memory errors are the sanitizer tree's job.

include_guard(GLOBAL)

# The runtime selection only takes effect under the NEW behaviour; refuse rather than pin nothing.
# A function keeps the policies of the file that defines it, which are those of the includer.
cmake_policy(GET CMP0091 _sushi_runtime_policy)
if(NOT _sushi_runtime_policy STREQUAL "NEW")
    message(FATAL_ERROR
        "SushiAbiPinning: policy CMP0091 is '${_sushi_runtime_policy}', so "
        "CMAKE_MSVC_RUNTIME_LIBRARY would be ignored. Raise cmake_minimum_required to 3.15 or later "
        "before including SushiBuild.")
endif()
unset(_sushi_runtime_policy)

# sushi_pin_abi()
#   Called after project(), before the first target, in the directory whose targets it covers.
#   Every build type takes the release C runtime, MultiThreadedDLL, which an ABI other than MSVC's
#   ignores. A Debug consumer of an imported target links its Release build, which shares that
#   runtime. The MSVC STL compiles with _ITERATOR_DEBUG_LEVEL 0, the level of its release
#   containers; libstdc++ and libc++ never read it.
function(sushi_pin_abi)
    if(ARGN)
        message(FATAL_ERROR "sushi_pin_abi(): it takes no argument; got '${ARGN}'.")
    endif()
    set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreadedDLL" PARENT_SCOPE)
    set(CMAKE_MAP_IMPORTED_CONFIG_DEBUG Release RelWithDebInfo MinSizeRel None "" PARENT_SCOPE)
    if(CMAKE_CXX_COMPILER_ID STREQUAL "MSVC" OR CMAKE_CXX_SIMULATE_ID STREQUAL "MSVC")
        add_compile_definitions("$<$<COMPILE_LANGUAGE:CXX>:_ITERATOR_DEBUG_LEVEL=0>")
    endif()
endfunction()
