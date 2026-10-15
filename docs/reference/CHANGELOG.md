# Changelog

## Unreleased

- 2026-10-16 — logging: Named every logger after its module and logged two silent failures, so `sushicore.typer_help` replaces `sushicore.help` (`provision/packages/base.py`, `provision/toolchains/adaptivecpp.py`).

## v0.9.0 — 2026-10-15

- 2026-10-15 — cmake: Let `ctest_run` leave out the tests whose labels match `exclude_label_regex`, such as quarantined ones (`cmake_driver.py`).
- 2026-10-15 — layout: Moved the package to `source/sushicore/` and each test to the mirror path of the unit it checks; an editable install is reinstalled with `pip install -e .` (`pyproject.toml`, `tests/`).
- 2026-10-15 — tests: Gave every unit a test file and enforced the size timeouts through pytest-timeout (`tests/`, `tests/conftest.py`).
- 2026-10-15 — ci: Split the pipeline into `ci.yml` (pre-merge checks, small and medium tests, `gate`) and `nightly.yml` (everything, quarantined tests reported), and made the release wait for CI (`.github/workflows/`).
- 2026-10-15 — tests: Labelled every test `small` or `medium`, registered the size markers and their timeouts, and made a test without a size fail collection (`tests/conftest.py`, `pyproject.toml`).
- 2026-10-14 — provision: Breaking change: Replaced the apt ROCm install with the newest AMD SDK tarball whose family covers every card, under `<home>/rocm` (`rocm_vendor.py`, `rocm_selection.py`).
- 2026-10-14 — provision: Read the AMD cards' ISAs from the amdgpu topology, with nothing installed (`amd_hardware.py`).
- 2026-10-14 — provision: Breaking change: Moved the choose, install and remember flow of CUDA into one vendor-blind `ChosenToolkitLocator` (`chosen_toolkit_locator.py`, `toolkit_vendor.py`, `cuda_vendor.py`).
- 2026-10-14 — provision: Breaking change: Replaced the CUDA 12.6.3 pin with the newest release the driver runs whose nvcc builds every card (`cuda_selection.py`, `CudaLocator`).
- 2026-10-14 — provision: Installed CUDA from NVIDIA's redistributable archives under `<home>/cuda`, without administrator rights (`cuda_toolkit_installer.py`, `cuda_redist.py`).
- 2026-10-14 — provision: Breaking change: Removed `WindowsCudaLocator` and `LinuxCudaLocator`, replaced by one `CudaLocator` (`gpu/cuda.py`).
- 2026-10-14 — provision: Removed `cuda` from the downloads a fragment pins, since its archives are checked against NVIDIA's published SHA-256 (`download_verifier.py`, `DEPENDENCY_FRAGMENT.md`).
- 2026-10-14 — provision: Made the doctor's `cuda` row look in `CUDA_PATH` first (`probe.py`).
