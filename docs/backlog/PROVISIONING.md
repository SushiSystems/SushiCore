# Provisioning

## Remaining work

| ID | Pri | State | Title | Done when | Blocked by | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RW-10 | P2 | open | Rewrite the build caches and the local configuration to the new root | the migration rewrites the build caches and each module's `cli/config.local.toml`, so the link at the old path can go |  | `docs/design/PROVISION/README.md` | 2026-10-19 |
| RW-11 | P2 | open | Lay toolchains out by version | toolchains install under `toolchains/<name>/<version>/` |  | `docs/design/PROVISION/README.md` | 2026-10-19 |
| RW-15 | P2 | open | Move the build, test, package and deploy scaffold here | the scaffold the AI and BLAS command lines each carry in their `cli/.../services/project.py` lives in this package |  | `docs/design/PROVISION/README.md` | 2026-10-19 |
| RW-16 | P2 | open | Remove `StackConfig.standalone_deps_dir` | `source/sushicore/stack_config.py` lacks it, one release after its last override is gone |  |  | 2026-10-19 |
| RW-54 | P2 | open | Provision every GPU vendor on a machine | `detect_gpu_vendor` returns every vendor present and the registry provisions a backend for each; a machine with an NVIDIA card and an AMD iGPU provisions only… |  |  | 2026-10-19 |
| RW-93 | P2 | open | Install winget packages through the winget manager in install_deps_step | install_deps_step.py builds no winget command line of its own |  | `source/sushicore/provision/install_deps_step.py` | 2026-11-17 |
| RW-98 | P3 | open | Prove the apt name translation in the adaptivecpp non-apt test again | the test uses a manager whose translate_apt changes a name and asserts the changed name |  | `tests/provision/toolchains/test_adaptivecpp.py` | 2026-11-17 |
| RW-101 | P2 | open | Carry licence consent through the CUDA install chain instead of the GpuStage gate | the toolkit locator and vendor take the consent and RedistToolkitInstaller refuses without it |  | `source/sushicore/provision/gpu_stage.py` | 2026-11-17 |
| RW-104 | P3 | open | Preview the transitively pinned libraries in a setup dry run | setup --dry-run lists a library pinned only by an unfetched library, read from its remote tag without cloning |  | `source/sushicore/provision/sushi_setup.py` | 2026-11-17 |
| RW-126 | P1 | open | Rebuild a consumer's objects when a package link moves to another digest | A build tree records the package digests it built against; a build whose links name others runs the clean target first, so no object keeps old headers |  | `source/sushicore/provision/sushi_packages/stable_link.py` | 2026-11-21 |
| RW-140 | P2 | open | Resolve the workspace of link and unlink with the pointer ModuleConfig and StackConfig use | link, unlink, ModuleConfig and StackConfig resolve one workspace through one function |  | `source/sushicore/provision/link_command.py` | 2026-11-21 |
| RW-141 | P2 | open | Read a dependency's fragment through the module's fragment key, not only the default path | pin_chain and closure_walk read the fragment path module_manifest names |  | `source/sushicore/provision/pin_chain.py` | 2026-11-21 |
| RW-147 | P1 | open | Hash only the files a library's package installs into its source key | A commit that changes only a library's cli/ or tests/ leaves its package digest unchanged, so a consumer rebuilds nothing |  | `source/sushicore/provision/sushi_packages/source_state.py` | 2026-11-21 |
| RW-153 | P1 | open | Build the Linux manager plan when a download verifier is given | managers_for on Linux with a verifier returns the distro managers and vcpkg, and sushitrack's Linux CI reaches its build |  | `source/sushicore/provision/manager_plans/linux.py` | 2026-11-21 |

## Known issues

| ID | Origin | Symptom | Workaround | Fix | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- |
| KI-34 | own | A pin bump leaves objects built on old headers; mixed layouts corrupt memory (ODR) | Rebuild the consumer tree from clean after every hub bump or install | RW-126 | `source/sushicore/provision/sushi_packages/stable_link.py` | 2026-11-21 |
