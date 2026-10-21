# GPU toolkit selection: report

**Status:** Shipped — 2026-10-14

What the selection rule of `docs/design/GPU_TOOLKIT_SELECTION.md` showed when it ran, moved here from
the design document. The real builds of RW-12 to RW-14 are not part of this report.

## The run on 2026-10-14

On the RTX 4050 (`sm_89`, driver ceiling 13.1) the rule chose 13.1.2, even though 13.4.3 was
published, and installed it. The merged root had `nvvm/libdevice/libdevice.10.bc` and
`lib/x64/cuda.lib`, and nvcc reported `release 13.1, V13.1.115`. The second run reused the
choice without reading the index.

Given a Pascal card next to an Ada one under a 13.4 ceiling, the 13.4.3 compiler listed `75` and
newer, and the 12.9.2 compiler listed `61`. The rule chose 12.9.2, a newer release than the old
12.6.3 pin.

The first run on Windows also hit the 260-character path limit inside `cuda_cccl`. The
installer unpacks through the `\\?\` extended-length form.

## The ROCm rule against AMD's listing

Checked against AMD's listing on 2026-10-14: `gfx1036`, the 7600X's iGPU, gets
`7.13.0-gfx103X-all`; `gfx1103` gets `7.13.0-gfx110X-all`; `gfx1151` gets the exact
`7.13.0-gfx1151`. An RDNA2 and an RDNA3 card together get nothing, because no one tarball
covers both.
