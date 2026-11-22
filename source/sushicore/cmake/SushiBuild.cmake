# SushiBuild.cmake
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.

# The one entry to the build policy and the helpers every Sushi C++ repository shares. The SushiCore
# CMake driver puts this folder on CMAKE_MODULE_PATH on every configure, so a repository writes
# include(SushiBuild) and calls what it needs. Including it defines functions and creates nothing,
# so it may come before project(); source/sushicore/cmake/README.md lists the functions.

include_guard(GLOBAL)

include("${CMAKE_CURRENT_LIST_DIR}/SushiSyclCompiler.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/SushiToolchain.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/SushiBuildPolicy.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/SushiAbiPinning.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/SushiPrecompiledHeaders.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/SushiTierLibraries.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/SushiSanitizers.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/SushiSyclTarget.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/SushiTestSizes.cmake")
