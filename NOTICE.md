# Notices

SushiCore is Copyright (c) 2026 Sushi Systems and licensed under the PolyForm Noncommercial
License 1.0.0; see `LICENSE`. The material below keeps its own licence.

No third-party code is vendored in this repository, no file is ported from third-party code,
and the package redistributes no third-party binary or data set.

## Python packages

pip installs these beside SushiCore; none is copied into the tree. `pyproject.toml` declares
the version floor. The licence is the one each package states in its own metadata, read from
the version in the last column.

| Package | Role | Declared | Source | Licence | Read from |
| --- | --- | --- | --- | --- | --- |
| rich | runtime | `>=13.0` | https://pypi.org/project/rich/ | MIT | 15.0.0 |
| tomli | runtime, Python below 3.11 | `>=2.0` | https://pypi.org/project/tomli/ | MIT | 2.4.0 |
| typer | extras `typer`, `test` | `>=0.12` | https://pypi.org/project/typer/ | MIT | 0.20.0 |
| click | extra `test` | `>=8.0` | https://pypi.org/project/click/ | BSD-3-Clause | 8.2.1 |
| pytest | extra `test` | `>=7.0` | https://pypi.org/project/pytest/ | MIT | 9.1.1 |
| setuptools | build | `>=77.0` | https://pypi.org/project/setuptools/ | MIT | 82.0.1 |

Packages those bring in:

| Package | Needed by | Licence | Read from |
| --- | --- | --- | --- |
| markdown-it-py | rich | MIT | 4.0.0 |
| mdurl | markdown-it-py | MIT | 0.1.2 |
| pygments | rich, pytest | BSD-2-Clause | 2.20.0 |
| shellingham | typer | ISC | 1.5.4 |
| typing-extensions | typer | PSF-2.0 | 4.15.0 |
| colorama | click and pytest on Windows | BSD-3-Clause | 0.4.6 |
| iniconfig | pytest | MIT | 2.3.0 |
| packaging | pytest | Apache-2.0 OR BSD-2-Clause | 26.3 |
| pluggy | pytest | MIT | 1.6.0 |

`exceptiongroup`, which pytest needs on Python below 3.11, was not installed where this list
was read; its licence is unverified.

## Software the provisioner installs

`sushicore.provision` downloads or installs these on the user's machine when a module CLI runs
`setup`. SushiCore ships none of them; each arrives from its vendor under the vendor's terms.
"unverified" marks a licence that was not read from the upstream source for this list.

| Software | Version | Source | Licence | Installed by |
| --- | --- | --- | --- | --- |
| Intel LLVM (DPC++) | latest release | https://github.com/intel/llvm | Apache-2.0 WITH LLVM-exception | `sushicore/provision/toolchains/intel_llvm.py` |
| Unified Runtime adapters, built from the Intel LLVM sources | the toolchain's commit | https://github.com/intel/llvm | Apache-2.0 WITH LLVM-exception | `sushicore/provision/gpu/adapter_builder.py` |
| AdaptiveCpp | v24.10.0 | https://github.com/AdaptiveCpp/AdaptiveCpp | BSD-2-Clause | `sushicore/provision/toolchains/adaptivecpp.py` |
| LLVM for Windows | 17.0.6 | https://github.com/llvm/llvm-project | Apache-2.0 WITH LLVM-exception | `sushicore/provision/toolchains/adaptivecpp.py` |
| LLVM, clang and lld from apt | 17: apt `clang-17`, `llvm-17-dev`, `libclang-17-dev`, `lld-17`; `clang`, `llvm` on other distributions | https://github.com/llvm/llvm-project | Apache-2.0 WITH LLVM-exception | `sushicore/provision/toolchains/adaptivecpp.py` |
| Boost.Context and Boost.Fiber | apt `libboost-context-dev`, `libboost-fiber-dev`; vcpkg `boost-context`, `boost-fiber` | https://github.com/boostorg/boost | BSL-1.0 | `sushicore/provision/toolchains/adaptivecpp.py` |
| vcpkg | default branch | https://github.com/microsoft/vcpkg | MIT | `sushicore/provision/packages/vcpkg.py` |
| CMake | latest release, or the apt package | https://github.com/Kitware/CMake | BSD-3-Clause | `sushicore/provision/packages/direct_download.py` |
| Ninja | latest release, or the apt package | https://github.com/ninja-build/ninja | Apache-2.0 | `sushicore/provision/packages/direct_download.py` |
| GoogleTest | apt `libgtest-dev`, vcpkg `gtest` | https://github.com/google/googletest | BSD-3-Clause | `sushicore/provision/manifests/base.deps.toml` |
| OpenCL ICD Loader | vcpkg `opencl` | https://github.com/KhronosGroup/OpenCL-ICD-Loader | Apache-2.0 | `sushicore/provision/manifests/base.deps.toml` |
| ocl-icd | apt `ocl-icd-opencl-dev`, `ocl-icd-libopencl1` | https://github.com/OCL-dev/ocl-icd | BSD-2-Clause | `sushicore/provision/manifests/base.deps.toml` |
| pkgconf | vcpkg `pkgconf` | https://github.com/pkgconf/pkgconf | ISC-style permission notice, upstream `COPYING` | `sushicore/provision/manifests/base.deps.toml` |
| pkg-config | apt `pkg-config` | the distribution's apt repository | unverified | `sushicore/provision/manifests/base.deps.toml` |
| GCC, g++, make | apt `build-essential` | the distribution's apt repository | unverified | `sushicore/provision/manifests/base.deps.toml` |
| Git for Windows | latest release, or winget `Git.Git` | https://github.com/git-for-windows/git | unverified | `sushicore/provision/packages/direct_download.py` |
| Doxygen | latest release, or winget `DimitriVanHeesch.Doxygen` | https://github.com/doxygen/doxygen | unverified | `sushicore/provision/packages/direct_download.py` |
| Visual Studio 2022 Build Tools | winget `Microsoft.VisualStudio.2022.BuildTools` | Microsoft | Microsoft's licence terms, unverified | `sushicore/provision/steps.py` |
| NVIDIA CUDA Toolkit | 12.6.3, apt `cuda-toolkit-12-6` | https://developer.download.nvidia.com/compute/cuda/ | NVIDIA's licence agreement, unverified | `sushicore/provision/gpu/cuda.py` |
| Intel oneAPI toolkit | 2026.0.0.193 | https://registrationcenter-download.intel.com/ | Intel's licence agreement, unverified | `sushicore/provision/toolchains/oneapi.py` |
| Intel oneAPI DPC++ compiler | apt `intel-oneapi-compiler-dpcpp-cpp` | https://apt.repos.intel.com/oneapi | Intel's licence terms, unverified | `sushicore/provision/steps.py` |
| Level Zero, the Intel OpenCL runtime and the oneAPI runtime libraries | apt `level-zero`, `intel-oneapi-runtime-opencl`, `intel-oneapi-runtime-libs` | https://apt.repos.intel.com/oneapi | unverified | `sushicore/provision/gpu/level_zero.py` |
| AMD ROCm | apt `rocm-hip-runtime-dev`, latest | https://repo.radeon.com/rocm/apt/latest | unverified | `sushicore/provision/gpu/rocm.py` |

The CUDA installer runs silently, the oneAPI installer runs with `--eula accept`, and winget
runs with `--accept-package-agreements`. Running `setup` therefore accepts those vendors' terms
for the user.

## Earlier versions

These were published under the Apache License 2.0 and stay available under it:

| Version | Commit | Published as |
| --- | --- | --- |
| 0.1.0 | `58ced89` | tag `v0.1.0`, PyPI |
| 0.2.0 | `e9a27ee` | tag `v0.2.0`, PyPI |
| 0.3.0 | `d2295c4` | tag `v0.3.0`, PyPI |
| 0.4.0 | `aa2c684` | tag `v0.4.0`, PyPI |
| 0.5.0, 0.6.0 | up to and including `9c0fce1` | commits on the GitHub `main` branch; no tag, not on PyPI |

Every commit before the one that adds this file carries the Apache License 2.0 text and stays
under it, the commits after `9c0fce1` included. The commit that adds this file and every later
commit are under the licence above. 0.7.0, when it is released from such a commit, is the first
version under it.
