# Code

## Remaining work

| ID | Pri | State | Title | Done when | Blocked by | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RW-20 | P2 | open | Split `provision/steps.py` | the four step classes of `source/sushicore/provision/steps.py`, 839 lines, sit in files of their own (Code C1) |  |  | 2026-10-19 |
| RW-23 | P2 | open | Move the process helper below the package managers | `packages/base.run` sits low enough for `provision/git_client.py` to sit below layer 4 |  |  | 2026-10-19 |
| RW-24 | P2 | open | Dispatch on platform and package manager through the contracts | no code switches on a platform or manager name where a contract exists (Code C2) |  |  | 2026-10-19 |
| RW-26 | P2 | open | Give the package one base error | failures raise one base error instead of a `bool`, `None` or a bare built-in, and `find_project_root` raises it in place of `SystemExit` (Code C7, Cli C8) |  |  | 2026-10-19 |
| RW-27 | P2 | open | Run every child process through one brick | the four runner copies and the 41 direct `subprocess` calls go through one brick that keeps stdout to events in machine mode (Code C8, Cli C4) |  |  | 2026-10-19 |
| RW-28 | P2 | open | Merge the duplicated probe tables and helpers in `provision` | each probe table and helper exists once (Code C9) |  |  | 2026-10-19 |
| RW-29 | P2 | open | Keep Rich behind the `Renderer` seam | `Console.console`, `diag.py`, `discovery.py` and the call sites in `provision` reach Rich only through `Renderer` (Code C10, Cli C6) |  |  | 2026-10-19 |
| RW-30 | P2 | open | Replace the global console and carry the level through `Renderer.line` | `provision/_output.py` holds no module console and a `line` event's level comes from the call, not the icon (Code C11, Cli C3) |  |  | 2026-10-19 |
| RW-31 | P2 | open | Shape the toolchain installers like the GPU backends | the toolchain installers share the GPU backends' contract (Code C12) |  |  | 2026-10-19 |
| RW-32 | P2 | open | Bring docstrings to the source comment rule | no public symbol lacks a docstring and none exceeds eight lines; 33 and 37 on 2026-10-19 (Code C13, Code C14, Code C21) |  |  | 2026-10-19 |
| RW-33 | P2 | open | Split the units that hold more than one responsibility | each unit outside `steps.py` that the audit named has one responsibility (Code C15) |  |  | 2026-10-19 |
| RW-34 | P2 | open | Type the untyped seams on the build side | the build-side seams the audit named carry types (Code C16) |  |  | 2026-10-19 |
| RW-35 | P2 | open | Stop tests reaching into private names | no test imports or calls a name with a leading underscore (Code C19) |  |  | 2026-10-19 |
| RW-36 | P2 | open | Remove hidden module state and apply the class-shape rules | no module keeps state outside an object, and classes outside `ui` and `help` follow the class-shape rules (Code C20, Code C22) |  |  | 2026-10-19 |
| RW-85 | P2 | open | Walk with walk_files in every shared checker that walks the tree | no shared checker calls rglob on the root; check_all in SushiStack finishes under 60 s |  |  | 2026-11-16 |
| RW-89 | P3 | open | Decide whether the Files port reads a modification time for filtered_run | Files carries modified_time on disk and in memory and run_filtered_shards takes no ModifiedTime, or the owner rules the two ports stay |  | `source/sushicore/testing/program_cases.py` | 2026-11-17 |
| RW-91 | P3 | open | Split register_backlog_commands into one function per command | commands.py registers each backlog command through its own function and no function there exceeds 60 lines |  | `source/sushicore/backlog/commands.py` | 2026-11-17 |
| RW-94 | P2 | open | Shape the provision contracts as one kind, Protocol or ABC | IDependencySource, IPackageManager, Step, Check, ConfigSink, ProvisionConfig and ToolkitLocator are all Protocols or all ABCs |  | `source/sushicore/provision/pipeline.py` | 2026-11-17 |
| RW-95 | P3 | open | Merge the write sequence that write_module and remove_module repeat | workspace.py writes a module file through one function both call |  | `source/sushicore/workspace.py` | 2026-11-17 |
| RW-96 | P3 | open | Delete prime_sudo, which nothing calls | packages/base.py and packages/__init__.py hold no prime_sudo |  | `source/sushicore/provision/packages/base.py` | 2026-11-17 |
| RW-97 | P3 | open | Bring the four :param: modules and five absolute imports to the package style | no module under provision uses :param: or imports sushicore.provision absolutely |  | `source/sushicore/provision/gpu/adapter_builder.py` | 2026-11-17 |
| RW-99 | P3 | open | Give pre_move_digest_writer a __main__ of its own and log in the library part | the writer's library function logs, and only a __main__ entry module writes to stdout or stderr |  | `source/sushicore/shared_tools/pre_move_digest_writer.py` | 2026-11-17 |
| RW-100 | P3 | open | Move the clock contracts into one shared test module | test_system_*_clock.py import their contract from a contract module, not from a sibling test file |  | `tests/provision/sushi_packages/test_wall_clock.py` | 2026-11-17 |
| RW-102 | P2 | open | Replace the module globals of download_verifier and home with injected seams | download_verifier.py and home.py hold no global statement |  | `source/sushicore/provision/home.py` | 2026-11-17 |
| RW-103 | P3 | open | Give IPackageManager a licence method so install_deps_step needs no isinstance check | install_deps_step.py holds no isinstance check against IWingetLicences |  | `source/sushicore/provision/install_deps_step.py` | 2026-11-17 |

## Known issues

| ID | Origin | Symptom | Workaround | Fix | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- |
| KI-31 | own | build_gate queue keeps a dead edge whose PID was reused, so every waiting compile hangs | Stop the build; the next run drops the dead entries | none, needs an owner decision on the identity key | `source/sushicore/build_gate.py` | 2026-11-12 |
