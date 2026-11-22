# CMakeLists.txt
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.

# One program under the build policy, the pinned ABI, the sanitizer target and the test-size step.
# Each probe line prints a variable a module sets, for the tests to read.

cmake_minimum_required(VERSION 3.29)
include(SushiBuild)
project(basic LANGUAGES CXX)

sushi_build_policy()
sushi_pin_abi()
sushi_sanitizers(basic)

if(NOT BASIC_SUITES)
    set(BASIC_SUITES suites_sized.cpp)
endif()
add_executable(probe probe.cpp)
target_link_libraries(probe PRIVATE basic_sanitizers)
sushi_check_test_sizes(probe SOURCES ${BASIC_SUITES})

message(STATUS "sushi-probe CMAKE_LINKER_TYPE=${CMAKE_LINKER_TYPE}")
message(STATUS "sushi-probe CMAKE_MSVC_RUNTIME_LIBRARY=${CMAKE_MSVC_RUNTIME_LIBRARY}")
message(STATUS "sushi-probe CMAKE_MAP_IMPORTED_CONFIG_DEBUG=${CMAKE_MAP_IMPORTED_CONFIG_DEBUG}")
