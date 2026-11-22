# SushiTestSizes.cmake
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.

# The build step that refuses a GoogleTest suite whose name carries no size. A test program
# registers its cases by the size prefix of their suite, so a suite without one would register no
# test and pass unseen.

include_guard(GLOBAL)

# sushi_check_test_sizes(<target> SOURCES <source>... [SUITE_REGEX <regex>])
#   Adds a step that <target> builds after: it reads every suite each source declares with TEST,
#   TEST_F, TEST_P, TYPED_TEST or TYPED_TEST_P, and fails the build at the first whose name does
#   not match <regex>. The default regex takes Small_, Medium_ and Large_, alone or after
#   Characterization_. The step reruns when a source changes.
function(sushi_check_test_sizes target)
    cmake_parse_arguments(ARG "" "SUITE_REGEX" "SOURCES" ${ARGN})
    if(ARG_UNPARSED_ARGUMENTS)
        message(FATAL_ERROR
            "sushi_check_test_sizes(${target}): unexpected argument(s) '${ARG_UNPARSED_ARGUMENTS}'.")
    endif()
    if(NOT ARG_SOURCES)
        message(FATAL_ERROR "sushi_check_test_sizes(${target}): SOURCES is required.")
    endif()
    if(NOT TARGET ${target})
        message(FATAL_ERROR "sushi_check_test_sizes(${target}): no target of that name exists.")
    endif()
    if(NOT ARG_SUITE_REGEX)
        set(ARG_SUITE_REGEX "^(Characterization_)?(Small|Medium|Large)_")
    endif()

    set(sources "")
    foreach(source IN LISTS ARG_SOURCES)
        get_filename_component(absolute "${source}" ABSOLUTE BASE_DIR "${CMAKE_CURRENT_SOURCE_DIR}")
        list(APPEND sources "${absolute}")
    endforeach()

    # The sources and the regex reach the script through a file, so no shell quotes them.
    set(settings "${CMAKE_CURRENT_BINARY_DIR}/${target}_sizes.cmake")
    set(stamp "${CMAKE_CURRENT_BINARY_DIR}/${target}_sizes.stamp")
    set(script "${CMAKE_CURRENT_FUNCTION_LIST_DIR}/SushiCheckTestSizes.cmake")
    set(SUSHI_TEST_SOURCES "${sources}")
    set(SUSHI_SUITE_REGEX "${ARG_SUITE_REGEX}")
    file(CONFIGURE OUTPUT "${settings}"
        CONTENT "set(SUSHI_TEST_SOURCES [==[@SUSHI_TEST_SOURCES@]==])\nset(SUSHI_SUITE_REGEX [==[@SUSHI_SUITE_REGEX@]==])\n"
        @ONLY)

    add_custom_command(
        OUTPUT "${stamp}"
        COMMAND ${CMAKE_COMMAND} "-DSUSHI_TEST_SIZES_SETTINGS=${settings}"
            "-DSUSHI_TEST_SIZES_STAMP=${stamp}" -P "${script}"
        DEPENDS ${sources} "${settings}" "${script}"
        COMMENT "Checking the test sizes of ${target}"
        VERBATIM)
    add_custom_target(${target}_sizes DEPENDS "${stamp}")
    add_dependencies(${target} ${target}_sizes)
endfunction()
