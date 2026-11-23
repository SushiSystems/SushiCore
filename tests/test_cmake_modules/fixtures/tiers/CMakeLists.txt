# CMakeLists.txt
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.

# Two tiers, low and high, with one STATIC module in low and two in high, and three programs: one
# linked through the tier libraries, one marked for the archives and one linked by plain CMake.
# TIERS_DECLARE_TWICE, TIERS_LINK_UPWARDS and TIERS_LINK_EARLY turn on the three calls the module
# refuses.

cmake_minimum_required(VERSION 3.29)
include(SushiBuild)
project(tiers LANGUAGES CXX)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

sushi_tier_libraries(PREFIX demo MACRO_PREFIX DEMO TIERS low high)
if(TIERS_DECLARE_TWICE)
    sushi_tier_libraries(PREFIX again MACRO_PREFIX AGAIN TIERS low)
endif()

add_library(low_mod STATIC low_mod.cpp)
sushi_tier_module(low_mod low)
if(TIERS_LINK_EARLY)
    add_executable(early app.cpp)
    sushi_tier_link(early PRIVATE high_mod)
endif()
add_library(high_mod STATIC high_mod.cpp)
target_include_directories(high_mod PUBLIC "${CMAKE_CURRENT_SOURCE_DIR}/high_headers")
sushi_tier_module(high_mod high)
add_library(high_peer STATIC high_peer.cpp)
sushi_tier_module(high_peer high)

sushi_tier_link(high_mod PUBLIC low_mod)
sushi_tier_link(high_peer PRIVATE high_mod)
if(TIERS_LINK_UPWARDS)
    sushi_tier_link(low_mod PRIVATE high_mod)
endif()

add_executable(shipped app.cpp)
sushi_tier_link(shipped PRIVATE high_peer)
add_executable(marked app.cpp)
sushi_tier_archives(marked)
sushi_tier_link(marked PRIVATE high_peer)
add_executable(plain app.cpp)
target_link_libraries(plain PRIVATE high_peer)
