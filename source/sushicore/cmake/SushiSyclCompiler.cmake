# SushiSyclCompiler.cmake
# SushiCore - https://github.com/SushiSystems/SushiCore
# Copyright (c) 2026-present Mustafa Garip & Sushi Systems
# Licensed under the Apache License 2.0. See LICENSE.

# What the C++ compiler of the configure says about SYCL: where its SYCL headers are, and whether
# it compiles SYCL at all. The build policy, the sanitizers and the SYCL target read it, so a flag
# a device pass rejects is wrapped in -Xarch_host only where a device pass exists.

include_guard(GLOBAL)

# sushi_sycl_include_dir(<out>)
#   Sets <out> to the include directory that holds sycl/sycl.hpp beside the compiler, read through
#   any symbolic link to its real path, or to an empty string when the compiler has none.
function(sushi_sycl_include_dir out)
    set(result "")
    if(CMAKE_CXX_COMPILER)
        get_filename_component(compiler "${CMAKE_CXX_COMPILER}" REALPATH)
        get_filename_component(bin_dir "${compiler}" DIRECTORY)
        get_filename_component(root_dir "${bin_dir}" DIRECTORY)
        if(EXISTS "${root_dir}/include/sycl/sycl.hpp")
            set(result "${root_dir}/include")
        endif()
    endif()
    set(${out} "${result}" PARENT_SCOPE)
endfunction()

# sushi_compiler_is_sycl(<out>)
#   Sets <out> to TRUE when the compiler is a SYCL compiler: icpx or icx, or a clang that ships the
#   SYCL headers beside it, as the intel/llvm build does. Sets it to FALSE otherwise.
function(sushi_compiler_is_sycl out)
    sushi_sycl_include_dir(include_dir)
    if(CMAKE_CXX_COMPILER_ID STREQUAL "IntelLLVM" OR include_dir)
        set(${out} TRUE PARENT_SCOPE)
    else()
        set(${out} FALSE PARENT_SCOPE)
    endif()
endfunction()

# sushi_host_flags(<out> <flag>...)
#   Sets <out> to the flags as the host compile takes them: each wrapped as SHELL:-Xarch_host <flag>
#   for a SYCL compiler, so its device pass never sees it, and unchanged for any other compiler.
function(sushi_host_flags out)
    sushi_compiler_is_sycl(is_sycl)
    set(result "")
    foreach(flag IN LISTS ARGN)
        if(is_sycl)
            list(APPEND result "SHELL:-Xarch_host ${flag}")
        else()
            list(APPEND result "${flag}")
        endif()
    endforeach()
    set(${out} "${result}" PARENT_SCOPE)
endfunction()
