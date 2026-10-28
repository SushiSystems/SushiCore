# Provisioning

## Remaining work

| ID | Pri | State | Title | Done when | Blocked by | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RW-8 | P2 | unmeasured | Run each module's real setup and build on the standalone layout | the real `setup` and build of `sr`, `sb`, `sa`, `sd`, `st` and, last, `se` have passed |  | `docs/design/STANDALONE_PROVISIONING/README.md` | 2026-10-19 |
| RW-9 | P2 | unmeasured | Run the hub root migration for real | the owner's `hub migrate`, each module's `doctor` and build, then `hub migrate --finalize` or `--rollback` have run |  | `docs/design/PROVISION/README.md` | 2026-10-19 |
| RW-10 | P2 | open | Rewrite the build caches and the local configuration to the new root | the migration rewrites the build caches and each module's `cli/config.local.toml`, so the link at the old path can go |  | `docs/design/PROVISION/README.md` | 2026-10-19 |
| RW-11 | P2 | open | Lay toolchains out by version | toolchains install under `toolchains/<name>/<version>/` |  | `docs/design/PROVISION/README.md` | 2026-10-19 |
| RW-12 | P2 | unmeasured | Build `sr` against a CUDA 13 toolkit on an Ada or newer card | the intel/llvm SYCL code and the Unified Runtime CUDA adapter have built against CUDA 13 |  | `docs/design/GPU_TOOLKIT_SELECTION/README.md` | 2026-10-19 |
| RW-13 | P2 | unmeasured | Build `sr` on the Pascal machine with the 12.9 toolkit | the selection gave 12.9.x in place of 12.6.3 and `sr` built |  | `docs/design/GPU_TOOLKIT_SELECTION/README.md` | 2026-10-19 |
| RW-14 | P2 | unmeasured | Install ROCm and build `sr` on an AMD card under Linux | the tarball's layout past its first 60 MB, `rocm_agent_enumerator` under `ROCM_PATH` and the HIP adapter have run |  | `docs/design/GPU_TOOLKIT_SELECTION/README.md` | 2026-10-19 |
| RW-15 | P2 | open | Move the build, test, package and deploy scaffold here | the scaffold the AI and BLAS command lines each carry in their `cli/.../services/project.py` lives in this package |  | `docs/design/PROVISION/README.md` | 2026-10-19 |
| RW-16 | P2 | open | Remove `StackConfig.standalone_deps_dir` | `source/sushicore/stack_config.py` lacks it, one release after its last override is gone |  |  | 2026-10-19 |
| RW-17 | P2 | open | Read a module's `fragment` key from `sushi-module.toml` | `setup` takes the fragment path a module declares instead of `DEFAULT_FRAGMENT` |  |  | 2026-10-19 |
| RW-18 | P2 | open | Clone a Sushi library that only a fetched library pins | `setup` fetches a Sushi library pinned by a fetched library and by no fragment here |  |  | 2026-10-19 |
| RW-51 | P2 | open | Read `use_vcpkg` | `stack_config.resolved_vcpkg` honours the `use_vcpkg` key the hub's defaults set per platform; the change reaches every command line that links this package |  |  | 2026-10-19 |
| RW-53 | P2 | open | Drop the doubled progress line | `InstallPipeline.run` reports each step once to a human; the JSON event stays and the Rich bar goes |  |  | 2026-10-19 |
| RW-54 | P2 | open | Provision every GPU vendor on a machine | `detect_gpu_vendor` returns every vendor present and the registry provisions a backend for each; a machine with an NVIDIA card and an AMD iGPU provisions only… |  |  | 2026-10-19 |
| RW-56 | P2 | open | Summarise cmake --install output in one line | a package install prints its command and one line counting the files it installed; a failed install prints cmake's whole output |  |  | 2026-10-29 |

## Known issues

| ID | Origin | Symptom | Workaround | Fix | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- |
