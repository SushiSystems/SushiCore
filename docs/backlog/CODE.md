# Code

## Remaining work

| ID | Pri | State | Title | Done when | Blocked by | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RW-26 | P2 | open | Give the package one base error | failures raise one base error instead of a `bool`, `None` or a bare built-in, and `find_project_root` raises it in place of `SystemExit` (Code C7, Cli C8) |  |  | 2026-10-19 |
| RW-29 | P2 | open | Keep Rich behind the `Renderer` seam | `Console.console`, `diag.py`, `discovery.py` and the call sites in `provision` reach Rich only through `Renderer` (Code C10, Cli C6) |  |  | 2026-10-19 |
| RW-30 | P2 | open | Replace the global console and carry the level through `Renderer.line` | `provision/_output.py` holds no module console and a `line` event's level comes from the call, not the icon (Code C11, Cli C3) |  |  | 2026-10-19 |
| RW-32 | P2 | open | Bring docstrings to the source comment rule | no public symbol lacks a docstring and none exceeds eight lines; 33 and 37 on 2026-10-19 (Code C13, Code C14, Code C21) |  |  | 2026-10-19 |
| RW-33 | P2 | open | Split the units that hold more than one responsibility | each unit outside `steps.py` that the audit named has one responsibility (Code C15) |  |  | 2026-10-19 |
| RW-34 | P2 | open | Type the untyped seams on the build side | the build-side seams the audit named carry types (Code C16) |  |  | 2026-10-19 |
| RW-35 | P2 | open | Stop tests reaching into private names | no test imports or calls a name with a leading underscore (Code C19) |  |  | 2026-10-19 |
| RW-36 | P2 | open | Remove hidden module state and apply the class-shape rules | no module keeps state outside an object, and classes outside `ui` and `help` follow the class-shape rules (Code C20, Code C22) |  |  | 2026-10-19 |
| RW-91 | P3 | open | Split register_backlog_commands into one function per command | commands.py registers each backlog command through its own function and no function there exceeds 60 lines |  | `source/sushicore/backlog/commands.py` | 2026-11-17 |
| RW-94 | P2 | open | Shape the provision contracts as one kind, Protocol or ABC | IDependencySource, IPackageManager, Step, Check, ConfigSink, ProvisionConfig and ToolkitLocator are all Protocols or all ABCs |  | `source/sushicore/provision/pipeline.py` | 2026-11-17 |
| RW-95 | P3 | open | Merge the write sequence that write_module and remove_module repeat | workspace.py writes a module file through one function both call |  | `source/sushicore/workspace.py` | 2026-11-17 |
| RW-97 | P3 | open | Bring the four :param: modules and five absolute imports to the package style | no module under provision uses :param: or imports sushicore.provision absolutely |  | `source/sushicore/provision/gpu/adapter_builder.py` | 2026-11-17 |
| RW-99 | P3 | open | Give pre_move_digest_writer a __main__ of its own and log in the library part | the writer's library function logs, and only a __main__ entry module writes to stdout or stderr |  | `source/sushicore/shared_tools/pre_move_digest_writer.py` | 2026-11-17 |
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

## Known issues

| ID | Origin | Symptom | Workaround | Fix | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- |
| KI-31 | own | build_gate queue keeps a dead edge whose PID was reused, so every waiting compile hangs | Stop the build; the next run drops the dead entries | none, needs an owner decision on the identity key | `source/sushicore/build_gate.py` | 2026-11-12 |
