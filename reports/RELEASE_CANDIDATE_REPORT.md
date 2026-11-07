# Release candidate status

**Status: NOT PREPARED.** No kernel image or hosted build exists for the current worktree, and CPU-001/CPU-002 have not been built or measured. The current state is an experiment branch with uncommitted work. It is not eligible for device installation, release, or production promotion.

## Repository identity

- Branch: `experiment/m0-m1-reproducible-baseline`
- HEAD at review: `1d7baee8d8363b1a1369bd1b3e654e30d5d5cc87`
- Worktree: modified workflow, Kconfig, schedutil source, and device collector; untracked reports and read-only schedutil collector. No commit was created.
- Build artifact location: none.

## Configuration and experiment state

The normal workflow selection remains `cpu_experiment=baseline`; CPU-001 and CPU-002 are opt-in build variants. Local `vayu_defconfig` plus `olddefconfig` checks resolved baseline, CPU-001, and CPU-002 configurations as expected. ThinLTO and existing performance configuration were retained. These checks validate Kconfig resolution only, not compilation or kernel behavior.

No performance experiment is accepted. No CPU/GPU frequency, thermal, charging, voltage, memory, or scheduler default has been selected for release. Thermal and battery protections remain untouched by the experiments described here.

## Release gates still open

1. Operator publishes the reviewed experiment worktree and records its resulting full source SHA.
2. Operator manually dispatches matched baseline, CPU-002, and CPU-001 Actions builds against that same source SHA and toolchain inputs; archive and inspect full provenance, config, logs, release, and checksums.
3. Resolve build warnings/failures and repeat a same-input build for reproducibility review.
4. Collect rooted vayu baseline and experiment telemetry, including schedutil tunables before/during/after, and perform randomized repeated A/B tests.
5. Complete boot, recovery/rollback, Android/root compatibility, suspend/resume, stability, security, thermal, sustained workload, latency, gaming, and battery/energy checks.
6. Accept or reject each experiment from measured results; integrate only accepted isolated changes, then build and validate the integrated candidate.
7. Technical lead reviews and explicitly authorizes any release or production promotion.

## Decision

Do not label, distribute, flash, or promote a release candidate from the current state. The next actionable step is hosted build validation after the operator publishes this worktree; physical validation follows only after matching artifacts exist and a recovery path is confirmed.


## Additional experiment since last status

MEM-002 adds an opt-in LZ4HC initial ZRAM compressor candidate, with `baseline` still selecting LZ4. Its effective config passed local `olddefconfig`, but no compilation or device measurement exists. This does not change release-candidate status: **NOT PREPARED**. Build and runtime/energy/thermal evaluation remain mandatory before integration.
