# SushiBuildPolicy.cmake
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.

# The build policy every Sushi C++ tree takes, with no option to leave it: lld as the linker, a
# compile_commands.json in the tree, and line tables only as the debug information of Debug.

include_guard(GLOBAL)
include("${CMAKE_CURRENT_LIST_DIR}/SushiSyclCompiler.cmake")

# sushi_build_policy()
#   Called once after project(), before the first target, in the directory whose targets it covers;
#   its subdirectories inherit it.
#
#   CMAKE_LINKER_TYPE LLD links with lld on every platform: ld.lld for a GNU-style driver and
#   lld-link for an MSVC-style one. lld links in parallel where ld.bfd and link.exe do not. CMake
#   reads CMAKE_LINKER_TYPE from 3.29, so an older CMake stops the configure.
#
#   Debug host code keeps line tables only: a stack trace gets its files and lines at a fraction of
#   full debug information's compile memory, object size and link time. CMake states -g for Debug
#   and the later -gline-tables-only overrides it. A SYCL compiler takes the flag through
#   -Xarch_host, since its device pass rejects it. RelWithDebInfo keeps full debug information, and
#   an MSVC-style frontend keeps what CMake states.
function(sushi_build_policy)
    if(ARGN)
        message(FATAL_ERROR "sushi_build_policy(): it takes no argument; got '${ARGN}'.")
    endif()
    if(NOT DEFINED PROJECT_NAME)
        message(FATAL_ERROR "sushi_build_policy(): call it after project(); no project is declared.")
    endif()
    if(CMAKE_VERSION VERSION_LESS 3.29)
        message(FATAL_ERROR
            "sushi_build_policy(): linking with lld through CMAKE_LINKER_TYPE needs CMake 3.29 or "
            "later; this configure runs CMake ${CMAKE_VERSION}. Install a newer CMake.")
    endif()

    set(CMAKE_LINKER_TYPE LLD PARENT_SCOPE)
    set(CMAKE_EXPORT_COMPILE_COMMANDS ON PARENT_SCOPE)

    if(CMAKE_CXX_COMPILER_ID MATCHES "Clang|IntelLLVM"
            AND NOT CMAKE_CXX_COMPILER_FRONTEND_VARIANT STREQUAL "MSVC")
        sushi_host_flags(line_tables -gline-tables-only)
        add_compile_options("$<$<AND:$<CONFIG:Debug>,$<COMPILE_LANGUAGE:CXX>>:${line_tables}>")
    endif()
endfunction()
