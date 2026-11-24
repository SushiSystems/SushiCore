# Code

## Remaining work

| ID | Pri | State | Title | Done when | Blocked by | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RW-29 | P2 | open | Keep Rich behind the `Renderer` seam | `Console.console`, `diag.py`, `discovery.py` and the call sites in `provision` reach Rich only through `Renderer` (Code C10, Cli C6) |  |  | 2026-10-19 |
| RW-94 | P2 | open | Shape the provision contracts as one kind, Protocol or ABC | IDependencySource, IPackageManager, Step, Check, ConfigSink, ProvisionConfig and ToolkitLocator are all Protocols or all ABCs |  | `source/sushicore/provision/pipeline.py` | 2026-11-17 |
| RW-95 | P3 | open | Merge the write sequence that write_module and remove_module repeat | workspace.py writes a module file through one function both call |  | `source/sushicore/workspace.py` | 2026-11-17 |
| RW-97 | P3 | open | Bring the four :param: modules and five absolute imports to the package style | no module under provision uses :param: or imports sushicore.provision absolutely |  | `source/sushicore/provision/gpu/adapter_builder.py` | 2026-11-17 |
| RW-100 | P3 | open | Move the clock contracts into one shared test module | test_system_*_clock.py import their contract from a contract module, not from a sibling test file |  | `tests/provision/sushi_packages/test_wall_clock.py` | 2026-11-17 |
| RW-102 | P2 | open | Replace the module globals of download_verifier and home with injected seams | download_verifier.py and home.py hold no global statement |  | `source/sushicore/provision/home.py` | 2026-11-17 |
| RW-103 | P3 | open | Give IPackageManager a licence method so install_deps_step needs no isinstance check | install_deps_step.py holds no isinstance check against IWingetLicences |  | `source/sushicore/provision/install_deps_step.py` | 2026-11-17 |
| RW-107 | P3 | open | Move status and install_command out of deps_fragment and fold digests into download_for | deps_fragment.py only reads fragments and the verifier reads digests through download_for |  | `source/sushicore/deps_fragment.py` | 2026-11-17 |
| RW-108 | P3 | open | Let RecordingRunner script raw bytes so a test can pin the byte decode of capture_bytes | RecordingRunner.capture_bytes answers scripted bytes and source_state has a test of a non-UTF-8 and a NUL-separated listing |  | `source/sushicore/proc_memory.py` | 2026-11-17 |
| RW-109 | P3 | open | Merge the two cmake path tables and the version probe timeout in provision | the cmake install paths are one Path table that probe and direct_download read, and the --version timeout is one constant checks and probe share |  | `source/sushicore/provision/probe.py` | 2026-11-17 |
| RW-110 | P3 | open | Key the GPU locators and the CUDA note on ITarget instead of the platform name | gpu/rocm.py, gpu/level_zero.py and detect_step.py read their per-platform values through ITarget or a target plan |  | `source/sushicore/provision/gpu/level_zero.py` | 2026-11-17 |
| RW-111 | P3 | open | Split resolve_local_config of the Windows probe plan into its steps | probe_plans/windows.py resolve_local_config is a short method over named steps, each tested |  | `source/sushicore/provision/probe_plans/windows.py` | 2026-11-17 |
| RW-112 | P2 | open | Pin oneAPI's order against the GPU stage and move its target switch into the plans | a test fixes whether oneAPI installs before or after the GPU stage, OneApiToolchain has no env.mgr is None branch, and ToolchainEnv names no toolchain |  | `source/sushicore/provision/toolchains/oneapi.py` | 2026-11-17 |
| RW-113 | P3 | open | Let detect read the toolchain registry's locate instead of its own probes | detect_step finds intel-llvm, AdaptiveCpp and oneAPI through TOOLCHAINS locate |  | `source/sushicore/provision/toolchains/registry.py` | 2026-11-17 |
| RW-114 | P3 | open | Type the provision console with one Console protocol instead of Any | provision steps, managers and functions take a console typed by one protocol that names header, progress, table, prompt and the line methods |  | `source/sushicore/provision/default_console.py` | 2026-11-17 |
| RW-116 | P3 | open | Give ModuleCycleError its own module and a provision layer | ModuleCycleError lives in a provision errors module listed in the layer table, and deps_fragment no longer defines it |  | `source/sushicore/deps_fragment.py` | 2026-11-17 |
| RW-120 | P3 | open | Type the console seam in the provision files the audit did not name | no provision module takes console: Any; each takes ProvisionConsole or a narrower protocol |  | `source/sushicore/provision/provision_console.py` | 2026-11-17 |
| RW-121 | P3 | open | Give each class in the multi-class files its own file | no file outside ui and help holds more than one public class beside its memory twin or its error |  | `source/sushicore/provision/doctor.py` | 2026-11-17 |
| RW-122 | P3 | open | Run a type checker over the package in check_all | check_all runs mypy or pyright over source/sushicore and it passes |  | `source/sushicore/tools/check_all.py` | 2026-11-17 |
| RW-123 | P3 | open | Give install_adaptivecpp a parameter object instead of about 20 parameters | install_adaptivecpp takes at most five parameters |  | `source/sushicore/provision/toolchains/adaptivecpp.py` | 2026-11-17 |
| RW-133 | P2 | blocked | Remove backlog import after its deprecation release, once the siblings take the tools | backlog import, BacklogImporter, ImportResult and the retired-files check are gone, and the shared tests of the siblings no longer pin them | external: the siblings take the tools of the release that deprecates backlog import | `docs/design/BACKLOG/README.md` | 2026-11-21 |
| RW-144 | P3 | open | Move RecordingApiBuild and FixedCommit out of the shipped package into the tests | no test double sits under source/sushicore |  | `source/sushicore/docs_bundle/api_reference.py` | 2026-11-21 |
| RW-145 | P3 | open | Ask the Renderer whether it is machine mode, and read the environment through Environment | Console tests no concrete renderer, and stack_config and build_admission read no os.environ |  | `source/sushicore/console.py` | 2026-11-21 |
| RW-164 | P1 | open | Make test_linux.py of probe_plans run no real compiler | test_a_configured_oneapi_root_with_setvars_is_recorded starts no process, and the Windows CI job no longer times out on it |  | `tests/provision/probe_plans/test_linux.py` | 2026-11-22 |

## Known issues

| ID | Origin | Symptom | Workaround | Fix | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- |
| KI-31 | own | build_gate queue keeps a dead edge whose PID was reused, so every waiting compile hangs | Stop the build; the next run drops the dead entries | none, needs an owner decision on the identity key | `source/sushicore/build_gate.py` | 2026-11-12 |
