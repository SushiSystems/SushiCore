# Provisioning reviews, checked against today's source

Backlog RW-4, job D8 of `PLAN.md`. The untracked folder `.superpowers/sdd/` holds 141 files from the
September provisioning work: 23 review files, 24 implementer reports, 21 briefs, 43 diff dumps and
30 support files. This report states each review finding in one sentence and checks it against the
source of 2026-11-17. The package has been rebuilt since then, so most findings name files that no
longer exist; those were checked by what replaced them. Review file names below omit the folder and
the `.md` suffix. `.superpowers/` is untouched; deleting it is the owner's call.

Source paths are under `D:/Projects/sushicore/source/sushicore/provision/` unless a row says otherwise.

## Findings that still hold

| Finding | File | Evidence today |
| --- | --- | --- |
| The package contracts mix ABCs (`IDependencySource`, `IPackageManager`, `Step`) with Protocols (`Check`, `ConfigSink`, `ProvisionConfig`, `ToolkitLocator`); siblings are not shaped alike. (final-review M1, task-11-review 6) | `fragments.py`, `packages/base.py`, `pipeline.py`, `doctor.py`, `sinks.py` | `class IDependencySource(ABC)` at `fragments.py:92`, `class IPackageManager(ABC)` at `packages/base.py:127`, `class Step(ABC)` at `pipeline.py:89`; `class Check(Protocol)` at `doctor.py:38`. |
| Four files document arguments in Sphinx `:param:` style while the rest use Google `Args:`. (final-review M2, task-9-review 3, task-13-review 4) | `gpu/windows_installer.py`, `gpu/adapter_builder.py`, `gpu/compiler_identity.py`, `toolchains/stamp.py` | `:param`, `:return:` or `:raises` occurs 12, 4, 3 and 10 times in them; nowhere else under `provision/`. |
| Import style is split: five modules import with the absolute `from sushicore.provision...` form, the rest use relative imports. (final-review M3, task-14-review minor 1) | `checks.py`, `fragments.py`, `pipeline.py`, `probe.py`, `system.py` | Each has a `from sushicore.provision` line. |
| Source carries comments that give a reason instead of what a thing does. (final-review M4, task-2-review 2, task-12-review 3, task-15-review C1) | `probe.py`, `toolchains/adaptivecpp.py` | `probe.py:220` ("would otherwise be parsed as rich markup"); `adaptivecpp.py:221,270,336,360,364` are reason comments. |
| Printed text still names hub commands or hub-era folders that module CLIs do not own. (task-12-review 4, task-11-review 7, final-review I6 remainder) | `toolchains/adaptivecpp.py`, `toolchains/intel_llvm.py`, `packages/direct_download.py`, `install_deps_step.py`, `uninstall_step.py`, `README.md`, `manifests/base.deps.toml` | `adaptivecpp.py:304,306,313` (`sr setup acpp`, `sr setup --profile normal`, "deps folder"); `intel_llvm.py:107` (`sr build --type asan`); `direct_download.py:210` ("already present in deps/tools"); `install_deps_step.py:186,190`; `uninstall_step.py:139,142`; `README.md:260` (`hub install`); `base.deps.toml:6`. |
| Em dashes remain in source strings and docstrings. (final-review M5, task-2-review 2, task-3-review 1 and 2) | `detect_step.py`, `gpu_stage.py`, `install_deps_step.py`, `packages/base.py`, `probe.py`, `selection.py`, `toolchains/adaptivecpp.py`, `toolchains/intel_llvm.py`, `toolchains/oneapi.py` | A search for the character matches these nine files. The README paragraph the review named is clean (0 matches). |
| `Doctor.render` and `render_table` take `console: object`; the seam has no type. (final-review M9, task-6-review minor) | `doctor.py`, `doctor_command.py`, `outcome.py` | `doctor.py:145,153`, `doctor_command.py:21`, `outcome.py:35`. |
| `probe.py` still has `del path` and a function-local `rich.markup` import. (task-2-review 6) | `probe.py` | `del path` at `probe.py:538`; local import at `probe.py:221`. |
| `prime_sudo` has no caller: it is defined and exported, and nothing under `source/` or `tests/` calls it. (task-11-review 5) | `packages/base.py`, `packages/__init__.py` | Defined at `base.py:44`, listed at `__init__.py:10,49`; no other hit. Unlinked item. |
| `_confirm_timeout` has no production caller; only its two tests reach it. Already RW-73 (job D5). (task-12-review 8) | `toolchains/adaptivecpp.py` | Defined at `adaptivecpp.py:48`; used at `tests/provision/toolchains/test_adaptivecpp.py:306,315`. |
| The hub's `config.set_toolchain` has no caller and repeats the factory's validation. (task-22-review minor, progress ledger) | `D:/Projects/sushistack/cli/sushihub/config.py` | `def set_toolchain` at line 328; no other match under `cli/`. Deleting it needs the owner's approval. |
| The adapter-builder test keeps its own `_ToolkitInstall` and `_GpuBackendSpec` stand-ins instead of the real backend types. (task-13-review warning) | `tests/provision/gpu/test_adapter_builder.py` | Dataclasses at lines 30 and 38. |
| `Registry.load` treats a directory at the registry path as an empty registry, and `save` replaces the file without `fsync`. (task-5-review M1, M3) | `registry.py` | `is_file()` test at line 85; `write_text` then `os.replace` at lines 224-226, no `fsync`. |
| The portable cmake and doxygen installers delete `tools_dir()/cmake` and `/doxygen` with no root guard; only uninstall and package removal call `home.is_removable_root`. (task-11-review f) | `packages/direct_download.py` | `shutil.rmtree(target, ignore_errors=True)` at lines 152 and 226; the guard is used at `uninstall_step.py:157` and `package_install.py:149` only. |
| `_install_vs_build_tools` builds its own `winget install` command line instead of going through the winget manager. (task-15-review a) | `install_deps_step.py` | `vs_cmd` list starting `"winget", "install"` at lines 253-260. |
| `_rewrite_stamp(root, mutate)` leaves `mutate` unannotated. (task-3-review minor) | `toolchains/stamp.py` | `def _rewrite_stamp(root: Path, mutate)` at line 38. |
| The test helper `dep` is defined twice instead of once in a conftest. (task-4-review 3) | `tests/provision/test_detect_step/test_detect.py`, `tests/provision/test_fragments/test_owner_order.py` | `def dep(` at lines 21 and 18. |
| `write_module` and `remove_module` repeat the same read, mutate, `setdefault`, `mkdir`, write sequence. (task-7-review a) | `source/sushicore/workspace.py` | Lines 187-194 and 202-211. |
| `DetectStep` calls `refresh_windows_path()` directly, so a Windows test run rewrites the process `PATH` unless the test patches it. (final-review M11) | `detect_step.py` | Call at `detect_step.py:244`. |

## Findings that no longer hold

| Finding | Evidence today |
| --- | --- |
| Dry-run configure crashed on a missing `probe.render_local_config` (final-review C1, task-15-review E1 backup loss). | `configure_step.py:13` imports it from `sinks`; `sinks.py:22,35` and `configure_step.py:55-57` back the file up first. |
| `setup` failed when the dependency root did not exist (final-review C2). | `lock.py:87` creates the parent directory. |
| The layering test skipped `from . import x` edges (final-review I1). | `tests/provision/test_layering.py` is gone; `tools/layering/check_layering.py` and `check_package_layers.py` run from `tools/check_all.py:65-66`. |
| `ProvisionConfig` lacked `ctest_exe` (final-review I2). | `config.py:20`. |
| Doctor never ran the fragment and stamp checks (final-review I3). | `module_checks.py:83,85` register `fragment_check` and `stamp_check(home.root())`. |
| `setup` ignored `depends_on` (final-review I4). | `closure.py:39,65` resolves the `depends_on` closure. |
| Underscore names were the package's public seams (final-review I5, task-11-review 8, task-21-review 1). | `packages/__init__.py` exports `run`, `download`, `tools_dir`, `gh_latest_asset`; no quoted underscore name remains in it. |
| Two User-Agent strings, one naming hub (final-review I6, task-3-review 5). | One constant, `system.py:20`, imported by the GPU installers. `sushiruntime-installer` appears nowhere. |
| No test for `~` in `SUSHISYSTEMS_HOME` (final-review I7, task-1-review M4). | `tests/provision/test_home.py:152`. |
| Table and JSON disagreed on a non-required failure; `doctor --for` accepted any group (final-review I8). | `doctor.py:75-99` (`shown_state` feeds both); `commands.py:18,60` validates against `GROUPS`. |
| Dead `_extract_tarball` duplicate (final-review I9, task-12-review 7). | No match for the name under `source/`. |
| Lock file descriptor leak and stale-lock races (final-review I10, task-5-review I1 to I3, task-5-rereview). | `lock.py:92-93,105-106` close the fd on any error; OS locking replaced PID polling. |
| Windows uninstall deleted under `tools/` before the root guard (final-review I11, task-15-review F1). | `uninstall_step.py:52,81,136` call `_root_is_safe` first; `home.is_removable_root` at `home.py:123`. |
| `_SHOW_PROGRESS` test toggle and `_managers_for` called twice (final-review M7, M8, task-16-review 3, 4). | No `_SHOW_PROGRESS` in source; `setup_command.py:70` builds `managers` once and passes it to both steps. |
| `home.root()` re-implemented `resolve_env_path` (final-review M10, task-1-review M1). | `home.py:56` resolves the root with its own seams; no `resolve_env_path` call remains. |
| `steps._first_available` unused (final-review out of scope). | `steps.py` is gone and the name has no match. |
| `install_intel_llvm` returned `Path` instead of hub's `str` (task-12-review 1). | Signature ends `-> str | None` at `intel_llvm.py:33`. |
| `install_gpu_stack` and the `_gh_*` helpers sat in `packages/base.py` (task-11-review 5). | They live in `packages/gpu_stack.py` and `packages/github_release.py`. |
| `fragment_check` had no timeout and caught too little (task-10-review). | `checks.py:154` catches `OSError, ValueError, TypeError, TimeoutExpired`. |
| `Registry.find` returned an arbitrary version; malformed entries raised a bare `KeyError`; non-BMP strings broke saves (task-5-review I4 to I6). | `registry.py:111-126` raises `RegistryError` on more than one version; the rereview confirms the other two. |
| The `link` command did not layer the workspace `[tool]` table (task-16-review warning). | `module_config.py:43-52,112` layers the workspace-shared config. |
| `test_doctor_filters_by_group` ran the real `standard_checks` (task-16-review warning). | `tests/provision/test_commands.py:91-103` injects `base_checks` through `MachineSeams`. |
| Uninstall left the legacy hub tree untouched with no word to the user (task-15-review F2). | `migrate.py` and `migration_*.py` move the legacy trees; `home.legacy_roots` stays for lookup. |
| `sudo_bash` docstring claimed sudo (task-2-review 5). | `system.py:63` now says it runs through bash. |
| Hub kept duplicate `WORKSPACE_HEADER` and `WORKSPACE_VERSION` (task-7-review warning). | No definition of either under `D:/Projects/sushistack/cli`. |
| Test files carried `# ----` banners (task-9-review 4) and 286 test functions lacked docstrings (docstring-pass-report). | No banner lines under `tests/provision/` or `provision/`; the docstring pass landed. |
| Provision code called `is_machine()`, which only hub's console had (is-machine-report). | `Console.is_machine` exists in `source/sushicore/console.py`. |

## Not re-verified

These minor findings name code the rebuild replaced and I did not trace each one to a successor:
task-9-review minors 1 and 2 (docstring length in `provisioning.py`), task-10-review minors (broad
`except Exception` at the old `checks.py:28`, `ninja_exe` computed early), task-12-review 5
(host-dependent LLVM tests; no `Program Files/LLVM` string remains in the adaptivecpp test, so
likely fixed), task-1-review M3 (`.sushistack` above the temp directory), task-14-review minor 3 (`#`
against `#:` field comments). The owner can treat them as low value.

## Files with no finding

Every other file in `.superpowers/sdd/` carries no separate finding:

- 24 implementer reports (`task-N-report` for N in 1 to 18 and 20 to 22, plus `docstring-pass-report`, `final-fix-report`, `is-machine-report`); their concerns are the same items the reviews above record, or rulings logged in `progress.md`.
- 21 task briefs (`task-N-brief`, N in 1 to 18 and 20 to 22).
- 43 diff dumps (every `review-*.diff` file).
- Support files: `.gitignore`, `commit-task.sh`, `git_diff_stat.txt`, `global-constraints.md`, `import-rewrite.md`, `move-rules.md`, `plan-path`, `progress.md`, `pytest_result.txt`.
- The `probe/` folder (7 scratch scripts and a lock file) and the `t22-baseline/` folder (7 baseline outputs and 7 after-run copies).
