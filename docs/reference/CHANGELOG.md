# Changelog

## Unreleased

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

## v0.8.1 — 2026-10-13

- 2026-10-13 — docs-bundle: Published the documentation bundle in a release; the PyPI 0.8.0 wheel lacks `sushicore/docs_bundle/`, so a consumer that imports it needs 0.8.1 (`pyproject.toml`, `sushicore/docs_bundle/`).
- 2026-10-07 — ci: Passed the repository's secrets to the CI the release job calls (`.github/workflows/release.yml`).
- 2026-10-07 — docs-bundle: Fixed the page order to read on through every document outside `agent/` and `archive/`, as the layout checker does (`page_order.py`, `DOCS_BUNDLE.md`).
- 2026-10-07 — ci: Added the release job that builds the documentation bundle after CI and attaches it to the tag's release (`.github/workflows/release.yml`, `ci.yml`).
- 2026-10-07 — docs-bundle: Fixed the page order refusing a page that the index reaches only through another page, by walking links as the layout checker does (`sushicore/docs_bundle/page_order.py`).
- 2026-10-07 — docs: Added the publish list, so this repository's manual is bundled for the documentation site (`docs/publish.toml`, `check_docs_layout.py`).
- 2026-10-07 — docs: Added the frequently asked questions page (`docs/guides/FAQ.md`).
- 2026-10-07 — docs-bundle: Added the documentation bundle producer and the `docs` command group a CLI registers (`sushicore/docs_bundle/`, `register_docs_commands`, `BundleProducer`).
- 2026-10-07 — describe: Listed a group that runs without a subcommand as a command of its own in the catalogue (`sushicore/describe.py`, `_flatten`).
- 2026-10-07 — cmake: Fixed a configure losing its `-D` values when the compiler path changed, by deleting the tree's cache before the run (`CMakeDriver.configure`, `compiler_changed`, `sushicore/cmake_cache.py`).
