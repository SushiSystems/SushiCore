# Provisioning

## Remaining work

| ID | Pri | State | Title | Done when | Blocked by | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RW-10 | P2 | open | Rewrite the build caches and the local configuration to the new root | the migration rewrites the build caches and each module's `cli/config.local.toml`, so the link at the old path can go |  | `docs/design/PROVISION/README.md` | 2026-10-19 |
| RW-11 | P2 | open | Lay toolchains out by version | toolchains install under `toolchains/<name>/<version>/` |  | `docs/design/PROVISION/README.md` | 2026-10-19 |
| RW-15 | P2 | open | Move the build, test, package and deploy scaffold here | the scaffold the AI and BLAS command lines each carry in their `cli/.../services/project.py` lives in this package |  | `docs/design/PROVISION/README.md` | 2026-10-19 |
| RW-16 | P2 | open | Remove `StackConfig.standalone_deps_dir` | `source/sushicore/stack_config.py` lacks it, one release after its last override is gone |  |  | 2026-10-19 |
| RW-18 | P2 | open | Clone a Sushi library that only a fetched library pins | `setup` fetches a Sushi library pinned by a fetched library and by no fragment here |  |  | 2026-10-19 |
| RW-54 | P2 | open | Provision every GPU vendor on a machine | `detect_gpu_vendor` returns every vendor present and the registry provisions a backend for each; a machine with an NVIDIA card and an AMD iGPU provisions only… |  |  | 2026-10-19 |
| RW-65 | P2 | open | Rename adapter_builder's CommandRunner so one name means one port | only proc.CommandRunner carries that name, and adapter_builder's runner port has its own |  | `source/sushicore/provision/gpu/adapter_builder.py` | 2026-11-05 |
| RW-66 | P3 | open | Split the package clock into a wall clock and a monotonic clock | PackageStore takes a wall clock and PackageResolver a monotonic one, each with its in-memory adapter |  | `source/sushicore/provision/sushi_packages/wall_clock.py` | 2026-11-05 |
| RW-67 | P2 | open | Give LinuxPackageManager an in-memory adapter beside its port | the three test copies of _FakeAptManager are gone and a contract test runs over the adapter |  |  | 2026-11-05 |
| RW-88 | P3 | open | Replace the package manager stand-in of test_adaptivecpp with InMemoryPackageManager | tests/provision/toolchains/test_adaptivecpp.py holds no _Manager stand-in |  | `tests/provision/toolchains/test_adaptivecpp.py` | 2026-11-17 |
| RW-90 | P2 | open | Pick the Linux manager in one order for detect, install and uninstall | dep_manager and available_linux_manager choose by K_LINUX_MANAGERS order and a test shows detect and install pick the same manager |  | `source/sushicore/provision/dependency_presence.py` | 2026-11-17 |
| RW-92 | P1 | open | Guard the portable cmake and doxygen removal with is_removable_root | direct_download.py removes tools_dir()/cmake and /doxygen only after home.is_removable_root, and a test refuses an unsafe root |  | `source/sushicore/provision/packages/direct_download.py` | 2026-11-17 |
| RW-93 | P2 | open | Install winget packages through the winget manager in install_deps_step | install_deps_step.py builds no winget command line of its own |  | `source/sushicore/provision/install_deps_step.py` | 2026-11-17 |
| RW-98 | P3 | open | Prove the apt name translation in the adaptivecpp non-apt test again | the test uses a manager whose translate_apt changes a name and asserts the changed name |  | `tests/provision/toolchains/test_adaptivecpp.py` | 2026-11-17 |
| RW-101 | P2 | open | Carry licence consent through the CUDA install chain instead of the GpuStage gate | the toolkit locator and vendor take the consent and RedistToolkitInstaller refuses without it |  | `source/sushicore/provision/gpu_stage.py` | 2026-11-17 |

## Known issues

| ID | Origin | Symptom | Workaround | Fix | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- |
