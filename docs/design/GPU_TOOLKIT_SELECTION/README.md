# GPU toolkit selection: the hardware picks the release

**Status:** Open — built and released in 0.9.0; the real builds of RW-12 to RW-14 are left
**About:** The estate pinned CUDA 12.6.3 on every machine, for one reason: CUDA 13 dropped Pascal (sm_6x), and the owner develops on a Pascal card, so a newer toolkit broke that build at the ptxas...
**Modules:** none

## Problem

The estate pinned CUDA 12.6.3 on every machine, for one reason: CUDA 13 dropped
Pascal (`sm_6x`), and the owner develops on a Pascal card, so a newer toolkit broke that build
at the ptxas link step. The pin kept Pascal working, but it also held every newer card back
and tied the whole estate to one machine. On Linux it needed an apt repository clamped to
`ubuntu2404`, and on Windows an installer that asked for administrator rights.

The aim of the estate is to depend on hardware as little as possible. Writing a version into
the code is the opposite of that.

## Decision

The toolkit release a machine gets is chosen from its own cards and driver. No release number is
written in the code.

### CUDA: the rule

The release installed is the newest one NVIDIA publishes that meets two conditions:

1. The driver runs it. `nvidia-smi` prints the newest CUDA version the driver supports, and a
   toolkit newer than that builds code the machine cannot run.
2. Its compiler builds for every card in the machine. The installer asks nvcc itself, with
   `nvcc --list-gpu-arch`, so no table of which release supports which architecture is kept
   here.

No CUDA version is written anywhere in the code. When NVIDIA publishes CUDA 14 the rule sees it
the same day, and when a card goes into or comes out of the machine the choice changes with it.

### ROCm: the rule

AMD publishes ROCm as SDK tarballs at `repo.amd.com/rocm/tarball/`, one per release and per
family of cards: `therock-dist-linux-gfx110X-all-7.13.0.tar.gz`. A family name is an ISA
pattern in which `X` stands for any character, and an optional variant such as `-all` or
`-dgpu`. The tarball installed is the one of the newest release whose family covers every AMD
card in the machine. When several families cover them, the one with the fewest wildcards wins,
then a family without a variant, then `-all`.

The cards come from the amdgpu kernel driver. Each agent under
`/sys/class/kfd/kfd/topology/nodes` reports a `gfx_target_version`, which spells the ISA
(110003 is `gfx1103`). Nothing has to be installed to read it.

### What it changes for the user

- Nothing needs administrator rights or `sudo`, on Windows or on Linux.
- Releases sit side by side. A system-wide CUDA is left alone. The user's `CUDA_PATH` points
  past it, and it stays the fallback when no release can be installed.
- The second run on the same hardware does not go to the network.
- `SUSHISYSTEMS_CUDA_RELEASE=12.6` installs the newest 12.6 release in place of the choice.
  Use it when a build has to target a card that is not in the machine.

## Design

### The shared flow

`gpu/chosen_toolkit_locator.py` holds the one flow every vendor follows. It reads the cards,
reuses the release recorded for them or chooses one, installs it under `<home>/<vendor>`, and
names the root in the vendor's variable for this process and in the user's variables.
`gpu/toolkit_vendor.py` is the `ToolkitVendor` protocol each vendor answers: how to read the
cards, which release fits them, how to install a release and what a toolkit root looks like.
The locator never names a vendor. Adding one adds a vendor file and a spec, and changes nothing
else.

### CUDA: how it works

| Step | Module | What it does |
| --- | --- | --- |
| Hardware | `gpu/cuda_hardware.py` | Reads each card's compute capability and the driver's CUDA ceiling from `nvidia-smi` |
| Index | `gpu/cuda_redist.py`, `cuda_release.py` | Lists the `redistrib_<version>.json` files under NVIDIA's `compute/cuda/redist/` and reads the archives and SHA-256 of one release |
| Choice | `gpu/cuda_selection.py` | Walks the majors from newest to oldest and asks the newest release of each major which architectures it builds for |
| Install | `gpu/cuda_toolkit_installer.py` | Downloads `cuda_nvcc`, `cuda_cudart` and `cuda_nvml_dev`, plus `cuda_crt`, `libnvvm` and `cuda_cccl` when the release publishes them, checks each one's SHA-256 and merges them into `<home>/cuda/<release>` |
| Vendor | `gpu/cuda_vendor.py` | Answers the `ToolkitVendor` protocol with the modules above |
| Spec | `gpu/cuda.py` | The backend spec, with a `ChosenToolkitLocator` over `CudaVendor` |

Only the newest release of each major is asked, because NVIDIA removes an architecture only in
a major release. A minor release can deprecate one but does not remove it. Each question
downloads one nvcc archive of about 30 MB, so a Pascal machine pays for two of them on its first
run and nothing after that. The archive of the release that gets chosen is kept and reused by
the install.

The merged folder has the same layout as a full install: `bin/nvcc`, `nvvm/libdevice`,
`include/cuda.h` and, on Windows, `lib/x64/cuda.lib`. SushiRuntime's locator reads `CUDA_PATH`
first on both platforms, and the Unified Runtime adapter build is given the same root.

The first run on Windows meets the 260-character path limit inside `cuda_cccl`, so the installer
unpacks through the `\\?\` extended-length form.

### ROCm: how it works

| Step | Module | What it does |
| --- | --- | --- |
| Hardware | `gpu/amd_hardware.py` | Reads each card's ISA from the kfd topology |
| Index | `gpu/rocm_tarball_index.py`, `rocm_package.py` | Reads the tarball names from AMD's listing and matches a family against an ISA |
| Choice | `gpu/rocm_selection.py` | Picks the newest tarball whose family covers every card |
| Install | `gpu/rocm_toolkit_installer.py` | Downloads the tarball and unpacks it into `<home>/rocm/<release>-<family>`; its top level is the ROCm root |
| Vendor | `gpu/rocm_vendor.py` | Answers the `ToolkitVendor` protocol, with `ROCM_PATH` and `SUSHISYSTEMS_ROCM_RELEASE` |
| Spec | `gpu/rocm.py` | The backend spec, Linux only |

The ROCm spec covers Linux alone. AMD lists Windows tarballs too, but intel/llvm ships no HIP
adapter on Windows, so nothing there would use them.

### The choice file

`<home>/<vendor>/choice.json` holds one object, written by `gpu/toolkit_choice_file.py`:

```json
{"format": 1, "fingerprint": "sm=89;driver=13.1", "platform": "windows-x86_64", "release": "13.1.2"}
```

The fingerprint lists every card's architecture and the driver's CUDA ceiling. A file of
another `format`, or one that does not parse, counts as absent: the choice is made again and the
file is rewritten.

### Limits

- AMD publishes no digest for its tarballs, so a ROCm download is trusted on HTTPS alone. Each
  tarball is about 5 GB.
- A family's variant is not read. `gfx110X-dgpu` may leave out the APU `gfx1103` that its
  pattern matches; when a release offers both, `-all` is preferred, but a release that offers
  only `-dgpu` is taken for an APU too.
- Cards that no single family covers, such as RDNA2 and RDNA3 together, get no ROCm.
- The choice sees only the cards in the machine. An `SR_CUDA_ARCH` that names a card the
  machine does not have, such as `61;89` on an Ada machine, needs the override.
- The first run needs the network. Without it the toolkit already in use stays in use, and
  without one of those the build takes the CPU path.

## Phases

| Id | Phase | State |
| --- | --- | --- |
| G1 | The shared locator, the CUDA rule and its installer | built |
| G2 | The ROCm rule and installer, Linux only | built |
| G3 | Real builds on hardware: `sr` against CUDA 13 (RW-12), on the Pascal machine with 12.9 (RW-13) and on an AMD card under Linux (RW-14) | planned |

### Work

<!-- work:begin -->
No open work.
<!-- work:end -->

## Open questions

- Do the intel/llvm SYCL toolchain and the Unified Runtime CUDA adapter build against a 13.x
  toolkit? CUDA 13 changed parts of the driver API, so this is the first thing to check on
  hardware. Settled by RW-12.
