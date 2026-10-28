# Code

## Remaining work

| ID | Pri | State | Title | Done when | Blocked by | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RW-20 | P2 | open | Split `provision/steps.py` | the four step classes of `source/sushicore/provision/steps.py`, 839 lines, sit in files of their own (Code C1) |  |  | 2026-10-19 |
| RW-21 | P2 | open | Move the setup and doctor command bodies out of `provision/commands.py` | `commands.py` registers commands and holds no command body |  |  | 2026-10-19 |
| RW-22 | P2 | open | Declare a module's fragment path once | one of `StackConfig.fragment` and `ModuleProvision.fragment` holds it |  |  | 2026-10-19 |
| RW-23 | P2 | open | Move the process helper below the package managers | `packages/base.run` sits low enough for `provision/git_client.py` to sit below layer 4 |  |  | 2026-10-19 |
| RW-24 | P2 | open | Dispatch on platform and package manager through the contracts | no code switches on a platform or manager name where a contract exists (Code C2) |  |  | 2026-10-19 |
| RW-25 | P2 | open | Remove the consumers' names and commands from the shared code | the provisioning commands take the `cli/` folder and the program name from the module, and `InstallContext.program` has no default `hub` (Code C3, Cli C18) |  |  | 2026-10-19 |
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
| RW-48 | P2 | open | Break the import cycle of `workspace` and `config_base` | neither module imports the other, inside a function or not (Code C4) |  |  | 2026-10-19 |
| RW-49 | P2 | open | Remove `_first_available` | `source/sushicore/provision/steps.py` lacks it (Code C24) |  |  | 2026-10-19 |

## Known issues

| ID | Origin | Symptom | Workaround | Fix | Source | Opened |
| --- | --- | --- | --- | --- | --- | --- |
