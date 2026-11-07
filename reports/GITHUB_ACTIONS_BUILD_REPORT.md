# GitHub Actions kernel build report

## Current publication/build status

- Repository origin: `git@github.com:Lvyana-ren/Xen-Kernel-Lab.git` (confirmed against GitHub repository `Lvyana-ren/Xen-Kernel-Lab`; the production repository is not configured as a remote).
- Branch: `experiment/m0-m1-reproducible-baseline`.
- Base commit before this publication: `1d7baee8d8363b1a1369bd1b3e654e30d5d5cc87`; local remote-tracking branch matched this commit at audit time.
- No Actions runs existed for this branch before publication.
- Build status: **NOT DISPATCHED / NO RUN URL / NO ARTIFACT** at report creation. The available GitHub connector has read, commit, ref update, artifact-download, and rerun operations, but no `workflow_dispatch` operation. Shell network sockets are denied by the current execution sandbox, so direct REST dispatch is unavailable here. Do not claim dispatch or build success.

## Pre-publication audit

- Current experiment branch work is uncommitted and preserved. Tracked edits: workflow, ZRAM Kconfig/default selection, schedutil Kconfig/source, and read-only device collector. Untracked files are the project reports and read-only schedutil collector. No staged changes existed.
- `.github/workflows/build-kernel.yml` is tracked as mode `100644` and is not ignored. No generated kernel image, archive, cache, or secret-pattern match was found. The largest new file is the saved prebuild `.config` (about 164 KiB).
- Origin is the Lab repository only. No production remote is configured.
- Workflow preflight uses `vayu_defconfig`; current baseline configuration keeps CPU/MEM experiments off, Xen release `4.14.357-Xen+3`, ThinLTO, and performance optimization. YAML/input assertions, embedded `bash -n`, both collector `sh -n` checks, and `git diff --check` passed before publication.
- Workflow inputs retain baseline defaults: source ref `16`, release flavor `xen`, generation `3`, CPU experiment `baseline`, memory experiment `baseline`, toolchain `clang-r547379`. Explicit alternatives remain available.
- Workflow now uploads only on success and names the uploaded artifact with device/toolchain/experiment/run identity. A ZIP is assembled only when the successful job has a nonempty kernel `Image`; the ZIP has a SHA-256 sidecar and is included in the artifact checksum manifest.

## Requested matched runs

Run 1 — baseline:

- `source_ref`: exact full SHA of the published experiment commit
- `release_flavor`: `xen`
- `release_generation`: `3`
- `cpu_experiment`: `baseline`
- `memory_experiment`: `baseline`
- `toolchain`: `clang-r547379`

Run 2 — toolchain comparison:

- Same exact source SHA and all other inputs as Run 1
- `toolchain`: `clang-r614150`

Do not select non-baseline CPU and memory experiments together; workflow validation rejects that combination. Do not treat source/config checks as a kernel build.

## Results

Run IDs/URLs, run commit SHA, compiler output, build status, final config SHA, image filename/size/SHA, ZIP filename/size/SHA, and downloaded artifact path remain **pending** because no dispatch operation is exposed to this agent. The current environment has no local `gh` executable and prohibits network sockets. There is no Termux download command until an artifact exists and is accessible from a reachable host.

## Next action

Use GitHub Actions UI or a separately authorized API-capable environment to dispatch the two listed runs against the pushed full commit SHA. Then download each successful run artifact to `artifacts/github-actions/`, inspect checksums and ZIP/image contents, and update this report with actual run metadata. Physical vayu boot, recovery, stability, thermal, battery, and benchmark validation remain separate and pending.
