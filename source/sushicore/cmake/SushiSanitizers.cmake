# SushiSanitizers.cmake
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.

# The sanitizer set host code is built with, as an INTERFACE target a tree links to every target
# of its own. A sanitizer lane changes one cache entry and no target's CMakeLists.txt.

include_guard(GLOBAL)
include("${CMAKE_CURRENT_LIST_DIR}/SushiSyclCompiler.cmake")

# sushi_sanitizers(<prefix> [OPTION <name>])
#   Creates the INTERFACE target <prefix>_sanitizers and the cache entry <name>, <PREFIX>_SANITIZE
#   by default, that names the sanitizers as -fsanitize= takes them, comma-separated: empty, the
#   default, adds nothing; "address,undefined" is the AddressSanitizer and UndefinedBehaviorSanitizer
#   lane and "thread" the ThreadSanitizer lane. Compiled code keeps its frame pointers, and an
#   undefined behaviour report stops the program, so it fails the test instead of passing with a
#   line in the log. A SYCL compiler takes every compile flag through -Xarch_host: the device pass
#   has no sanitizer runtime for every device a build targets. An MSVC-style driver is refused.
function(sushi_sanitizers prefix)
    cmake_parse_arguments(ARG "" "OPTION" "" ${ARGN})
    if(ARG_UNPARSED_ARGUMENTS)
        message(FATAL_ERROR
            "sushi_sanitizers(${prefix}): unexpected argument(s) '${ARG_UNPARSED_ARGUMENTS}'.")
    endif()
    if(TARGET ${prefix}_sanitizers)
        message(FATAL_ERROR "sushi_sanitizers(${prefix}): ${prefix}_sanitizers already exists.")
    endif()
    if(ARG_OPTION)
        set(option ${ARG_OPTION})
    else()
        string(TOUPPER "${prefix}_SANITIZE" option)
    endif()
    set(${option} "" CACHE STRING
        "Sanitizers for host code, as -fsanitize= takes them: empty, address,undefined or thread.")

    add_library(${prefix}_sanitizers INTERFACE)
    set(sanitizers "${${option}}")
    if(sanitizers STREQUAL "")
        return()
    endif()
    if(NOT sanitizers MATCHES "^[a-z_-]+(,[a-z_-]+)*$")
        message(FATAL_ERROR
            "${option}='${sanitizers}' is not a comma-separated list of sanitizer names, such as "
            "address,undefined or thread.")
    endif()
    if(MSVC OR CMAKE_CXX_COMPILER_FRONTEND_VARIANT STREQUAL "MSVC")
        message(FATAL_ERROR "${option}=${sanitizers} needs a GNU-style compiler driver.")
    endif()

    set(flags "-fsanitize=${sanitizers}" -fno-omit-frame-pointer)
    if(sanitizers MATCHES "(^|,)undefined(,|$)")
        list(APPEND flags -fno-sanitize-recover=undefined)
    endif()
    sushi_host_flags(host_flags ${flags})
    target_compile_options(${prefix}_sanitizers INTERFACE ${host_flags})
    target_link_options(${prefix}_sanitizers INTERFACE "-fsanitize=${sanitizers}")
endfunction()
