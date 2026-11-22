# SushiCheckTestSizes.cmake
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.

# The script the step of sushi_check_test_sizes() runs. It fails when a suite in the sources has no
# size its regex accepts, and writes the stamp when every suite has one. The settings file sets
# SUSHI_TEST_SOURCES and SUSHI_SUITE_REGEX.
#
#   cmake -DSUSHI_TEST_SIZES_SETTINGS=<file> -DSUSHI_TEST_SIZES_STAMP=<file> -P SushiCheckTestSizes.cmake

if(NOT DEFINED SUSHI_TEST_SIZES_SETTINGS OR NOT DEFINED SUSHI_TEST_SIZES_STAMP)
    message(FATAL_ERROR
        "SushiCheckTestSizes: pass -DSUSHI_TEST_SIZES_SETTINGS=<file> and "
        "-DSUSHI_TEST_SIZES_STAMP=<file>.")
endif()
include("${SUSHI_TEST_SIZES_SETTINGS}")

foreach(source IN LISTS SUSHI_TEST_SOURCES)
    file(READ "${source}" text)
    string(REGEX MATCHALL "(TEST|TEST_F|TEST_P|TYPED_TEST|TYPED_TEST_P)\\([ \t\r\n]*[A-Za-z0-9_]+"
        declarations "${text}")
    foreach(declaration IN LISTS declarations)
        string(REGEX REPLACE "^[A-Z_]+\\([ \t\r\n]*" "" suite "${declaration}")
        if(NOT suite MATCHES "${SUSHI_SUITE_REGEX}")
            message(FATAL_ERROR
                "${source}: the suite ${suite} carries no size; a suite name matches "
                "${SUSHI_SUITE_REGEX}.")
        endif()
    endforeach()
endforeach()
file(WRITE "${SUSHI_TEST_SIZES_STAMP}" "")
