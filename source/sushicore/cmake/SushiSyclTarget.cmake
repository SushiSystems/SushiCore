# SushiSyclTarget.cmake
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.

# The SYCL policy of a target that compiles against SushiRuntime, in one place. On the intel-llvm
# toolchain a unit compiles for the device only when its target names it in DEVICE_SOURCES; every
# other unit compiles for the host alone, with the toolchain's SYCL headers on its include path.
# Measured on SushiEngine, the device pass is 50% to 72% of the wall time of a unit with no kernel.
# On the other toolchains add_sycl_to_target() is the toolchain's own function and takes the
# whole target. SushiRuntime_SYCL_TOOLCHAIN and add_sycl_to_target() come from the SushiRuntime
# package, so it is found first.

include_guard(GLOBAL)
include("${CMAKE_CURRENT_LIST_DIR}/SushiSyclCompiler.cmake")

# sushi_sycl_device_options(<out_compile> <out_link>)
#   Sets <out_compile> to the options a device unit compiles with on intel-llvm and <out_link> to
#   the options a SYCL link takes: -fsycl, the device targets SushiRuntime resolved for this build
#   (read from SushiRuntime::gpu_offload, none when it publishes none) and the device optimisation
#   level, -O3 in every build type. A Debug build compiles host code at -O0; a device pass that
#   followed it would make the kernels the tests run too slow to test. -Xarch_device reaches the
#   frontend of every device target. On the link -O3 reaches only the device link, since the host
#   objects are already compiled.
function(sushi_sycl_device_options out_compile out_link)
    set(compile -fsycl)
    set(link -fsycl)
    if(TARGET SushiRuntime::gpu_offload)
        get_target_property(runtime_compile SushiRuntime::gpu_offload INTERFACE_COMPILE_OPTIONS)
        get_target_property(runtime_link SushiRuntime::gpu_offload INTERFACE_LINK_OPTIONS)
        if(runtime_compile)
            list(APPEND compile ${runtime_compile})
        endif()
        if(runtime_link)
            list(APPEND link ${runtime_link})
        endif()
    endif()
    list(APPEND compile "SHELL:-Xarch_device -O3")
    list(APPEND link -O3)
    set(${out_compile} "${compile}" PARENT_SCOPE)
    set(${out_link} "${link}" PARENT_SCOPE)
endfunction()

# sushi_sycl_target(<target> [DEVICE_SOURCES <source>...] [HOST_ONLY])
#   Applies the SYCL policy to <target>. On intel-llvm:
#     - with DEVICE_SOURCES, those sources compile for the device and every other unit for the host
#       with the SYCL headers. A unit that submits a kernel but is left off the list compiles clean
#       and fails at run time with "kernel not found", so name a whole folder rather than files.
#     - with HOST_ONLY, no unit compiles for the device; every unit gets the SYCL headers.
#     - with neither, every unit compiles for the device.
#   The link takes the device options in each case, since it pulls the device images out of the
#   objects and archives it links. A static library hands them to the targets that link it, where
#   that link runs. On another toolchain add_sycl_to_target() takes the whole target, and the
#   DEVICE_SOURCES are the sources it is told about.
function(sushi_sycl_target target)
    cmake_parse_arguments(ARG "HOST_ONLY" "" "DEVICE_SOURCES" ${ARGN})
    if(ARG_UNPARSED_ARGUMENTS)
        message(FATAL_ERROR
            "sushi_sycl_target(${target}): unexpected argument(s) '${ARG_UNPARSED_ARGUMENTS}'.")
    endif()
    if(ARG_HOST_ONLY AND ARG_DEVICE_SOURCES)
        message(FATAL_ERROR
            "sushi_sycl_target(${target}): HOST_ONLY and DEVICE_SOURCES exclude each other.")
    endif()
    if(NOT TARGET ${target})
        message(FATAL_ERROR "sushi_sycl_target(${target}): no target of that name exists.")
    endif()

    if(NOT SushiRuntime_SYCL_TOOLCHAIN STREQUAL "intel-llvm")
        if(NOT COMMAND add_sycl_to_target)
            message(FATAL_ERROR
                "sushi_sycl_target(${target}): no SYCL toolchain is loaded; find the SushiRuntime "
                "package before applying the SYCL policy.")
        endif()
        if(ARG_DEVICE_SOURCES)
            add_sycl_to_target(TARGET ${target} SOURCES ${ARG_DEVICE_SOURCES})
        else()
            add_sycl_to_target(TARGET ${target})
        endif()
        return()
    endif()

    sushi_sycl_device_options(device_compile device_link)
    get_target_property(type ${target} TYPE)
    if(type STREQUAL "STATIC_LIBRARY" OR type STREQUAL "OBJECT_LIBRARY")
        set(link_scope INTERFACE)
    else()
        set(link_scope PRIVATE)
    endif()

    if(NOT ARG_DEVICE_SOURCES AND NOT ARG_HOST_ONLY)
        target_compile_options(${target} PRIVATE ${device_compile})
        target_link_options(${target} ${link_scope} ${device_link})
        return()
    endif()

    sushi_sycl_include_dir(include_dir)
    if(include_dir STREQUAL "")
        message(FATAL_ERROR
            "sushi_sycl_target(${target}): no sycl/sycl.hpp beside ${CMAKE_CXX_COMPILER}, so a unit "
            "compiled for the host alone cannot find the SYCL headers.")
    endif()
    target_include_directories(${target} SYSTEM PRIVATE "$<BUILD_INTERFACE:${include_dir}>")
    target_compile_definitions(${target} PRIVATE SYCL_DISABLE_FSYCL_SYCLHPP_WARNING)

    if(ARG_DEVICE_SOURCES)
        # A source's COMPILE_OPTIONS does not expand SHELL: groups, so each group becomes its words.
        set(source_options "")
        foreach(option IN LISTS device_compile)
            if(option MATCHES "^SHELL:(.*)$")
                separate_arguments(group NATIVE_COMMAND "${CMAKE_MATCH_1}")
                list(APPEND source_options ${group})
            else()
                list(APPEND source_options "${option}")
            endif()
        endforeach()
        set_property(SOURCE ${ARG_DEVICE_SOURCES} TARGET_DIRECTORY ${target}
            APPEND PROPERTY COMPILE_OPTIONS ${source_options})
    endif()
    target_link_options(${target} ${link_scope} ${device_link})
endfunction()
