# Glossary

| Word | Meaning |
| --- | --- |
| Base fragment | `sushicore/provision/manifests/base.deps.toml`, the fragment naming what the SYCL modules share; a module asks for it with `ModuleProvision.uses_base` |
| Binary install | An unpacked release, recognised by `sushi-release.json` at its root; it gets `doctor` alone |
| Brick | A unit with one responsibility that can be detached, re-attached and rebuilt without touching its neighbours |
| Capability | What a `provides` key in a fragment names, such as `sycl-toolchain`; any one member that is present satisfies it |
| Check | One named test the doctor runs; it has a group, a `required` flag and a result of `ok`, `warn`, `fail` or `skip` |
| Checkout | A source tree of a module, recognised by its root marker |
| Closure | The fragments `setup` reads for one module: its own and, through `depends_on`, those of every module it builds on |
| Component | A frozen dataclass in `sushicore/ui` with `render(theme)`; one terminal element per file |
| Console | The facade a CLI prints through (`info`, `error`, `table` and the rest); it turns each call into a renderer call |
| Dependency root | The one folder per machine that holds installed toolchains and tools: `SUSHISYSTEMS_HOME`, else `~/.sushisystems` |
| Doctor | The read-only report of a module's checks; exit code 1 when a required check fails |
| Event | One JSON object on one line of stdout in machine mode |
| Fragment | A `sushistack.deps.toml` file: one table per dependency a repository needs, plus a `[module]` table |
| Group | The job a check guards: `build`, `test`, `infer` or `eval` |
| Help model | `HelpModel`, a help screen as data, read from a Click or Typer command by `build_model` |
| Icon set | The prefixes printed before a line, as data; a preset or a registered one |
| Legacy tree | A hub dependency tree from before the dependency root: `<workspace>/dependencies` or the folder `SUSHISTACK_DEPS_DIR` names; read, never written |
| Link pointer | The `[link] workspace` entry in a module's `cli/config.local.toml` that names the workspace the module is linked to |
| Machine mode | A console built with `JsonRenderer`; stdout carries events and nothing else |
| Marker | What marks a root by being there: the `.sushistack` folder for a workspace, the file named in a module's profile for a checkout |
| Module CLI | The CLI of one module: `sr`, `se`, `sa`, `sb`, `sd` or `st`; `hub` is the workspace's CLI |
| Profile | `ModuleProfile`, what one CLI says about itself: name, command, environment prefix, root marker |
| Registry | `registry.toml` in the dependency root, the record of what is installed and which modules use it |
| Renderer | An object with the eight drawing methods `Console` calls; `RichRenderer`, `PlainRenderer` and `JsonRenderer` ship |
| Selection | `ToolchainSelection`, which toolchain components one `setup` run installs, derived from the fragments and what is on the machine |
| Sink | `ConfigSink`, where the configure step writes its result: a workspace's `[tool]` table or a module's `cli/config.local.toml` |
| Stamp | `.sushi_toolchain.json`, the file inside an installed toolchain that says what it is |
| Theme | The style tokens of the console, as data; a preset or a registered one |
| Work folder | `docs/agent/<YYYY_MM_DD>_<WORK_NAME>/`, holding the `SPEC.md`, `PLAN.md` and `REPORT.md` of one piece of agent work |
| Workspace | A folder holding `.sushistack/workspace.toml`, which records the modules linked to it and the tools they share |
