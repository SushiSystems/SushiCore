# SushiToolchain.cmake
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.

# What a top-level Sushi C++ project settles before project() probes the compiler: the vcpkg
# toolchain file on Windows, and clang++ as the compiler when the configure names none. The
# libraries a project pulls in as subprojects find both settled, whichever reaches them first.

include_guard(GLOBAL)

# sushi_vcpkg_toolchain()
#   On a Windows host, points CMAKE_TOOLCHAIN_FILE at the vcpkg tree VCPKG_ROOT names, from the
#   cache or else the environment, unless the configure set a toolchain file itself. The CLI passes
#   -DVCPKG_ROOT from the tree its setup found, so a workspace layout is read there and not here.
#   Does nothing on another host.
function(sushi_vcpkg_toolchain)
    if(NOT CMAKE_HOST_WIN32)
        return()
    endif()
    if((NOT DEFINED VCPKG_ROOT OR VCPKG_ROOT STREQUAL "") AND DEFINED ENV{VCPKG_ROOT})
        set(VCPKG_ROOT "$ENV{VCPKG_ROOT}" CACHE PATH "Path to vcpkg root")
    endif()
    if(VCPKG_ROOT AND (NOT DEFINED CMAKE_TOOLCHAIN_FILE OR CMAKE_TOOLCHAIN_FILE STREQUAL ""))
        set(CMAKE_TOOLCHAIN_FILE "${VCPKG_ROOT}/scripts/buildsystems/vcpkg.cmake"
            CACHE FILEPATH "vcpkg toolchain file")
    endif()
endfunction()

# sushi_default_compiler()
#   Sets CMAKE_CXX_COMPILER to the clang++ on the search path when the configure names no compiler,
#   so a plain configure lands on the intel-llvm toolchain SushiRuntime defaults to. A configure
#   that names one, such as acpp or icx-cl, keeps it.
function(sushi_default_compiler)
    if(NOT DEFINED CMAKE_CXX_COMPILER OR CMAKE_CXX_COMPILER STREQUAL "")
        find_program(SUSHI_CLANGXX NAMES clang++)
        if(SUSHI_CLANGXX)
            set(CMAKE_CXX_COMPILER "${SUSHI_CLANGXX}" CACHE FILEPATH "CXX compiler")
        endif()
    endif()
endfunction()

# sushi_toolchain_bootstrap()
#   Called before project(): sushi_vcpkg_toolchain(), then sushi_default_compiler().
function(sushi_toolchain_bootstrap)
    if(ARGN)
        message(FATAL_ERROR "sushi_toolchain_bootstrap(): it takes no argument; got '${ARGN}'.")
    endif()
    sushi_vcpkg_toolchain()
    sushi_default_compiler()
endfunction()
