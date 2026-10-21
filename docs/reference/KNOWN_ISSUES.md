# Known issues

Next id: KI-26

## Releases

### KI-1 Versions 0.5.0 and 0.6.0 were never tagged or published
- Origin: own
- Where: `pyproject.toml`
- Cause: the versions were raised without a release
- Recognise: PyPI goes from 0.4.0 to 0.7.0, and no changelog section records 0.5.0 to 0.7.0
- Workaround: pin 0.4.0 or 0.7.0
- Fix: none, the versions were never published

## Machine output

### KI-2 With the emoji, minimal or none icons every warning is reported as info
- Origin: own
- Where: `source/sushicore/renderer.py`
- Cause: `_level_from_prefix` reads a JSON `line` event's level from the icon prefix
- Recognise: a warning or an error arrives as `"level": "info"` in machine mode
- Workaround: use the default icon set in machine mode
- Fix: RW-30

### KI-3 The doctor's `table` event carries Rich markup
- Origin: own
- Where: `source/sushicore/provision/doctor.py`
- Cause: the state cells are written as `[success]ok[/success]` and `[error]FAIL[/error]`
- Recognise: a consumer of the event shows the brackets
- Workaround: strip `[...]` tags in the consumer
- Fix: RW-41

### KI-4 In machine mode stdout carries a child process's output
- Origin: own
- Where: `source/sushicore/proc.py`, `source/sushicore/provision/steps.py`,
  `source/sushicore/provision/system.py`, `source/sushicore/provision/toolchains/oneapi.py`
- Cause: `Runner.run` and the provisioning steps let the child inherit stdout
- Recognise: lines that are not JSON events among the events
- Workaround: skip lines that do not parse as JSON
- Fix: RW-27

### KI-5 `setup`, `link` and `unlink` end without a `result` event
- Origin: own
- Where: `source/sushicore/provision/commands.py`
- Cause: no exit helper emits it
- Recognise: the last event of the run is not `result`
- Workaround: read the exit code
- Fix: RW-37

## Commands

### KI-7 A command run outside a checkout prints plain text and no console line
- Origin: own
- Where: `source/sushicore/module_config.py`
- Cause: `find_project_root` raises `SystemExit(message)`
- Recognise: the message reaches stderr without the console's icon or a machine-mode event
- Workaround: run the command inside a checkout
- Fix: RW-26

### KI-8 `link` registers a workspace that is not one and can leave half a link
- Origin: own
- Where: `source/sushicore/provision/commands.py`
- Cause: `--workspace PATH` is taken unchecked, and the module pointer is written before the
  workspace's `[modules]` table without undo
- Recognise: a new `.sushistack/workspace.toml` under the path given, or a pointer with no
  `[modules]` entry after a failed run
- Workaround: give `--workspace` a real workspace root; run `unlink` after a failure
- Fix: RW-39

### KI-9 `doctor --for` hides its groups and `--yes` has no `-y`
- Origin: own
- Where: `source/sushicore/provision/commands.py`, `source/sushicore/provision/doctor.py`
- Cause: the help does not list the groups, `infer` and `eval` belong to one module, and the
  option is declared without its short form
- Recognise: `doctor --help` names no group; `-y` works in `hub` and fails here
- Workaround: read `GROUPS` in `doctor.py`; spell `--yes`
- Fix: RW-6

### KI-10 The provisioning commands assume a `cli/` folder and the `hub` program
- Origin: own
- Where: `source/sushicore/provision/commands.py`, `source/sushicore/provision/pipeline.py`
- Cause: the folder is fixed and `InstallContext.program` defaults to `hub`
- Recognise: a module whose command line lives elsewhere gets its sink written under `cli/`
- Workaround: keep the command line in `cli/`
- Fix: RW-25

### KI-12 `clean` says "removed" when the build tree is still there
- Origin: own
- Where: `source/sushicore/cmake_driver.py`
- Cause: `CMakeDriver.clean_tree` removes with `ignore_errors=True` and does not look again
- Recognise: the folder exists after a successful-looking clean, usually a file held open
- Workaround: close the program holding the file and clean again
- Fix: RW-43

### KI-13 An unknown `color` or `background` falls back in silence
- Origin: own
- Where: `source/sushicore/config.py`
- Cause: those values are taken as strings unchecked, while an unknown `theme` or `icons` is an
  error
- Recognise: a misspelt value changes nothing and prints nothing
- Workaround: check the spelling against the manual
- Fix: RW-5

## Downloads

### KI-16 Setup accepts third-party licences on the user's behalf
- Origin: own
- Where: `source/sushicore/provision/toolchains/oneapi.py`,
  `source/sushicore/provision/packages/winget.py`, `source/sushicore/provision/steps.py`,
  `source/sushicore/provision/gpu/cuda_toolkit_installer.py`
- Cause: the oneAPI installer runs with `--eula accept`, winget with
  `--accept-package-agreements`, and the CUDA archives unpack without NVIDIA's licence shown
- Recognise: no licence text appears during setup
- Workaround: read the vendors' licences before running setup
- Fix: RW-46

### KI-17 ROCm SDK tarballs are used unverified
- Origin: dependency
- Cause: AMD publishes no digest for them
- Recognise: the download is trusted on HTTPS alone
- Workaround: none
- Source: `source/sushicore/provision/gpu/rocm_toolkit_installer.py`

### KI-18 A failed probe returns nothing and records nothing
- Origin: own
- Where: `source/sushicore/provision/probe.py`
- Cause: the `except` at line 83 returns `None`
- Recognise: doctor reports a tool missing without saying why
- Workaround: run the tool by hand
- Fix: RW-47

## Documentation and layout

### KI-21 `AGENTS.md` tells the reader to build with `se`
- Origin: own
- Where: `AGENTS.md`
- Cause: it moved from the old agent instruction file under `docs/` unchanged and names
  commands and folders of another repository
- Recognise: line 41 names `se build` and `se editor`
- Workaround: build with this repository's own commands
- Fix: RW-1

### KI-22 The open plans cite old paths and absolute paths
- Origin: own
- Where: `docs/agent/2026_09_25_HUB_ROOT_MIGRATION/PLAN.md`,
  `docs/agent/2026_10_04_STANDALONE_PROVISIONING/PLAN.md`, `docs/design/STANDALONE_PROVISIONING/README.md`
- Cause: the hub root migration plan moved into the tree after it was cited, the provisioning
  design moved on 2026-10-05, and the standalone plan was written with paths on one machine
- Recognise: citations of the old `plans` and `specs` folders under `docs/agent/`, 43 paths
  starting `D:/`, and 45 unticked boxes in the standalone plan
- Workaround: find the document by name under `docs/`
- Fix: RW-38
