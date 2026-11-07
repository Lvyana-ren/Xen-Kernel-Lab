# Xen-Kernel Lab mission status report

## 1. Executive summary

This mission is **NOT COMPLETE**. M0 CI integrity and M1 read-only collection preparation are present; static CPU research exists and broader subsystem source research has been added. No Actions build, kernel build, physical-device collection, trace, benchmark, or battery/thermal measurement is available. Therefore there is no evidence to accept performance tuning. The project is blocked from final engineering promotion by hosted build evidence and physical Poco X3 Pro access.

The appropriate current engineering outcome is to preserve the vendor WALT/schedutil/KGSL/Qualcomm thermal stack, keep all runtime values unchanged, complete CI and device baselines, then run isolated measurements before selecting optimizations.

## 2. Original baseline characteristics

- Baseline branch `16`: commit `bf6ac1247feda28293062995d445506b050aec8a`.
- Experiment branch: `experiment/m0-m1-reproducible-baseline`; current HEAD `1d7baee8d8363b1a1369bd1b3e654e30d5d5cc87`, matching `origin` at initial audit.
- Source target: Linux 4.14.357, ARM64, Poco X3 Pro vayu, SM8150.
- Experiment changes relative to `origin/16` are CI workflow, two exact build patch files, and read-only collector infrastructure. No CPU/GPU/memory/storage/thermal/power runtime tuning source/config was changed.
- Static config enables WALT, SchedTune, scheduler core_ctl, schedutil, Qualcomm CPU OSM, KGSL/Adreno TZ, ZRAM with LZ4 source default, CMA, thermal/CPU/devfreq/TSENS support and power-supply/charger paths.
- Runtime observations: **none**. The repository contains no device capture or benchmark results.

## 3. Milestone completion state

| Milestone | State | Evidence / blocker |
|---|---|---|
| M0 build infrastructure | Implemented; acceptance pending | Source selection, patch context/hash, config and release checks, artifact checksums and 30-day retention exist. No Actions run is listed. Toolchain/runner/action/apt dependencies remain mutable. |
| M1 baseline preparation | Infrastructure ready; physical baseline blocked | Read-only collector, controlled protocol and CPU/device guides. No rooted vayu or device transport. Collector coverage was extended for storage, CPU isolation and schedtune scalar data. |
| M2 source research | Static source research complete for CPU and initial GPU/memory/storage/thermal/power paths | CPU report is detailed; subsystem reports mark runtime unknowns. Source work cannot identify measured bottlenecks. |
| M3 CPU experiments | CPU-001 and CPU-002 opt-in variants implemented; schedutil source path and three effective configs validated | No kernel build or device profile yet; evaluation blocked on hosted CI and physical device. |
| M4 GPU experiments | Source path reviewed; experiment selection deferred | KGSL/msm-adreno-tz target decision uses secure TZ; no frame/GPU/thermal trace. |
| M5 memory/storage experiments | Source/config path reviewed; no tuning change | No pressure, ZRAM runtime stats, I/O latency or device data. |
| M6 thermal/power experiments | Source/DTS paths reviewed; safety settings preserved | No thermal/current/energy timeline. |
| M7 cross-subsystem | Not started | Needs independently validated candidates first. |
| M8 latency/gaming | Not started | No touch/frame traces or frame-time results. |
| M9 efficiency/sustained | Not started | No energy or thermal steady-state measurements. |
| M10 integration/RC | Not started | Build, boot and regression evidence absent. |
| M11 physical promotion gate | Added; blocked | Requires actual rooted vayu and technical lead review before production promotion. |

## 4. Optimization areas investigated

Source/config audits and reports cover WALT/fair placement/load balance/wakeup, SchedTune, schedutil and Qualcomm OSM, core_ctl and hyp_core_ctl, CPU idle/LPM, KGSL/Adreno devfreq, ZRAM/reclaim/CMA/LLCC, block schedulers, TSENS/LMH/cooling and charger/battery overlays, and gaming frame-pacing methodology. Each source fact is separated from runtime state. See CPU_RESEARCH.md, GPU_RESEARCH.md, MEMORY_STORAGE_RESEARCH.md, THERMAL_POWER_RESEARCH.md and GAMING_LATENCY_RESEARCH.md.

## 5. Source modifications and accepted changes

Current experiment branch includes:

- `.github/workflows/build-kernel.yml`: source/ref verification, exact patch application, config/release checks, build evidence capture and artifact provenance.
- `ci-patches/0001-hyp-core-ctl-include-cpu-header.diff`: include visibility for the driver’s cpu_subsys reference.
- `ci-patches/0002-xen-release-extraversion.diff`: exact `EXTRAVERSION=-openela` to empty value for Xen release naming.
- `scripts/xen-baseline/collect-device.sh`: read-only collection of device runtime state. This mission adds CPU isolated/nohz masks, bounded schedtune scalar probes, `/proc/diskstats` and block queue/stat snapshots.
- `drivers/cpufreq/Kconfig`, `kernel/sched/cpufreq_schedutil.c`, and `.github/workflows/build-kernel.yml`: uncommitted CPU-001 (no up/down limits) and CPU-002 (no up limit only) schedutil variants. Neither is accepted for promotion.

ZRAM source remains LZ4 and the workflow asserts that value without rewriting it. The baseline build continues to use the existing schedutil transition-delay defaults. CPU-001 changes only the opt-in experiment variant's initial governor rate limits; no CPU frequency limits, thermal trips, charging, voltage, GPU clock, or memory tuning was introduced.

## 6. Accepted and rejected optimizations

CPU-001 and CPU-002 are implemented for evaluation only. No optimization has been accepted or rejected by measurement. GPU, memory/storage and thermal/power source paths were reviewed; no safe default change is justified without runtime evidence.

Accepted performance optimizations: **none**; none met the measurement requirement.

Rejected/deferred decisions:

- Do not replace WALT or schedutil based on unrelated devices/kernels.
- Do not raise CPU/GPU clocks or boost values without response, energy and thermal evidence.
- Do not change core_ctl thresholds, idle states, memory reclaim, ZRAM algorithm/size, storage scheduler or thermal policy without corresponding measurements.
- Do not modify charge or thermal safety controls.

No performance comparison, thermal comparison, battery comparison, or frame-time comparison exists. No improvement is claimed.

## 7. Build and validation results

No successful/failed kernel build is recorded for the experiment branch; GitHub Actions run query returned zero runs. `gh`, Clang and LLD are unavailable in this environment, and the GitHub connector provides read/fetch but no workflow-dispatch operation. No image or build artifact exists for this HEAD.

Local static validation performed during this mission: repository/ref audit, workflow YAML parsing and source-input assertions, embedded Bash syntax, patch applicability/idempotence, collector shell syntax, mock collector test of newly added data paths/missing-node statuses, and `git diff --check`. No full build was run.

ThinLTO remains selected by the existing workflow: `CONFIG_LTO`, `CONFIG_LTO_CLANG`, `CONFIG_THINLTO` and performance optimization are checked after olddefconfig; actual build log must show `-flto=thin` and LLD. Current hosted effective config/build evidence remains pending.

## 8. Security, stability and Android compatibility

Static review found the collector writes only to its chosen output directory, not device controls. Exact build patches fail on unexpected context. The CI runner, apt versions, Clang branch and Actions v4 tags remain mutable and are captured with per-run provenance rather than fully pinned. No lockdep, sanitizer, security scan, build, boot, suspend, stress or Android compatibility test was possible. No claim of runtime stability or security validation is made.

## 9. Device validation still required

The operator must use `DEVICE_VALIDATION_REQUIRED.md`, `DEVICE_BASELINE_GUIDE.md` and `RUNTIME_BASELINE.md`. Required data includes CPU policy/driver/residency, WALT/SchedTune/core control, idle residency, KGSL levels/utilization, memory/ZRAM/reclaim, storage latency, thermal/cooling, battery energy, sustained loads, suspend/resume, frame pacing and wakeup latency. No device result may be inferred from this VPS.

## 10. Final kernel configuration and artifacts

The final selected runtime config is the existing vayu baseline plus the existing workflow’s local version, ThinLTO and performance compiler settings. No final generated `.config` exists for this HEAD because CI has not run. There is no final kernel image or artifact location.

## 11. Final engineering decisions

| Subsystem | Changed | Preserved / rejected | Evidence | Safe to promote? |
|---|---|---|---|---|
| CPU/scheduler | No runtime behavior change. | Preserve WALT, SchedTune, schedutil, placement, core_ctl and current limits. Reject speculative tuning. | Source/config only; no device traces. | No performance patch exists to promote. |
| GPU | No change. | Preserve KGSL and Adreno TZ policy; reject clock/limit changes. | Config/source only; no frame/GPU trace. | No. |
| Memory/ZRAM | Collector adds observations only. | Preserve source LZ4 and current runtime policy; reject compressor/size changes. | Source config only. | Collector may proceed after CI; runtime changes no. |
| Storage | Collector adds read-only queue/counter snapshots. | Preserve runtime scheduler and queue values. | Defconfig lists available schedulers, not active choice. | Collector only, pending CI/device test. |
| Thermal/power/charging | No change. | Preserve all protections and limits. | Static DTS/config only; no temperatures/current. | No runtime change to promote. |
| Build/CI | Explicit patch/provenance and validation workflow. | Preserve compiler release and ThinLTO; no auto dispatch or source promotion. | Static workflow checks; no hosted artifacts. | Ready for operator CI, not yet accepted as a successful build. |

## 12. Remaining risks and recommended next steps

1. Manually dispatch the experiment branch in GitHub Actions with source_ref set to the experiment branch, Xen flavor, generation 3. Verify patch provenance, final config, release, ThinLTO command evidence and all artifact checksums.
2. Run a second identical source/toolchain/config build if reproducibility comparison is required; document expected nondeterministic fields.
3. Collect rooted vayu baseline under controlled conditions and preserve raw data.
4. Review actual measurements and nominate one falsifiable, reversible experiment at a time.
5. Complete build/boot/security/stability and performance/energy/thermal gates before M10/M11 promotion review.

**Final status: INCOMPLETE, externally blocked by hosted CI and physical device access.** The branch remains an experiment branch. No performance gain or production readiness is claimed.

## 13. Known limitations

The toolchain branch, hosted image, apt repositories and Actions major tags are mutable. No CI artifact exists, current effective config cannot be confirmed with the intended Clang on this host, and no device values, tracepoints, benchmarks, energy readings or thermal trajectories have been captured. Static research cannot determine what Android userspace changes after boot.

## 14. Device validation still required

Rooted vayu collection is pending. Follow `DEVICE_VALIDATION_REQUIRED.md`; preserve metadata, manifest and raw files. Cover CPU, GPU, memory/ZRAM, storage, thermal/power, gaming/frame time, latency, sustained performance, idle and suspend/resume. No data should be substituted from another device.

## 15. Final kernel configuration

No final generated config exists. Intended build config remains vayu defconfig plus existing workflow-selected Xen `LOCALVERSION`, ThinLTO and performance optimization. Runtime scheduler, frequency, GPU, memory, thermal and charging settings remain unchanged.

## 16. Final source commit SHA

At initial mission inspection: `1d7baee8d8363b1a1369bd1b3e654e30d5d5cc87`. Documentation and collector changes made during this mission are uncommitted, so this SHA does not include the current worktree edits. A final source SHA can only be stated after authorized commit/publish; no commit was made here.

## 17. Final branch

`experiment/m0-m1-reproducible-baseline`. The branch tracked `origin` at initial inspection. The current worktree now contains mission documentation and a read-only collector extension; it has not been committed or pushed.

## 18. Final artifact locations

No kernel image/build artifact exists. CI workflow is `.github/workflows/build-kernel.yml`; exact patches are in `ci-patches/`; device collector is `scripts/xen-baseline/collect-device.sh`. Mission reports are under `reports/`, especially `ROADMAP.md`, `BUILD_VALIDATION_REPORT.md`, `DEVICE_VALIDATION_REQUIRED.md` and this report.

## 19. Remaining risks

Key risks are unverified build and patch application in Actions, mutable build dependencies, unverified Android merged DT/userspace behavior, and completely unknown runtime/thermal/energy baseline. No critical regression is known because no runtime policy change was made, but absence of a reported regression is not stability validation.

## 20. Recommended next steps

Publish the reviewed experiment branch state, manually dispatch CI, audit all provenance and image checksums, then collect rooted-device baseline data. Use those data to choose one subsystem experiment at a time. Maintain rollback image and require boot, suspend, security/stability, frame pacing, sustained, thermal and energy comparisons before production promotion.

## FINAL ENGINEERING DECISIONS

See the subsystem-by-subsystem table in section 11. No runtime optimization is currently safe to promote. The CI and collector infrastructure can be considered for promotion only after successful hosted validation and operator review; M0/M1 physical acceptance remains incomplete.
# Current execution update — 2026-11-07

The roadmap remains in progress at M3. CPU-001 and CPU-002 are implemented as opt-in experiments: CPU-001 removes initial up/down rate limits; CPU-002 removes only the initial up limit and retains the driver-derived down limit. The workflow default `baseline` preserves existing behavior. Neither experiment is accepted as an optimization.

Changed tracked kernel/build files in this execution: `drivers/cpufreq/Kconfig`, `kernel/sched/cpufreq_schedutil.c`, `.github/workflows/build-kernel.yml`. Existing uncommitted collector changes and prior reports remain preserved. Added CPU-001/CPU-002 experiment specifications and updated the roadmap, experiment registry, optimization matrix, decision log, GPU, memory/storage, thermal/power, build validation and final reports.

Validation: workflow YAML parsed; all embedded Bash run blocks passed `bash -n`; collector passed `sh -n`; `vayu_defconfig` and `olddefconfig` in `/tmp` verified baseline, CPU-001, and CPU-002 configs, including mutually exclusive symbol behavior; `git diff --check` passed. The workflow's conflicting-symbol check was adjusted after observing Kconfig omits an invisible symbol. No kernel build, hosted Actions run, physical-device test, performance measurement, commit or push was performed. GitHub Actions workflow-dispatch capability and local `clang`/`ld.lld` are unavailable here; the changed workflow must be published by an operator before CI can consume it.

Subsystem review: KGSL `msm-adreno-tz` gates on accumulated 5 ms total / 1 ms busy samples and delegates ordinary decisions to secure TZ; no threshold change is justified without frame-correlated device data. ZRAM remains LZ4 in source with runtime configuration unknown. Thermal/LMH paths constrain CPU/GPU but final merged DT/ROM runtime is unknown. No GPU, memory/storage, thermal, power or charging source setting was changed.

Next: operator publishes the experiment-branch changes, dispatches matched builds with `cpu_experiment=baseline`, `sugov_no_up_rate_limit`, and `sugov_no_rate_limit`, then runs device comparisons using the CPU experiment guides. M3 remains incomplete until physical response, energy, thermal, stability and sustained-workload results determine accept/reject. Do not promote CPU-001/002 based on configuration or build success alone.

## Current execution update — schedutil runtime validation

Added `scripts/xen-baseline/collect-schedutil.sh`, a read-only TSV capture tool. It records run label and before/during/after phase, device/kernel metadata, policy membership, governor, current frequency, available and min/max limits, transition latency, and active schedutil up/down tunables. It supports the OSM per-policy directory and a global-tunables fallback; missing, permission-denied, and non-schedutil cases remain distinct. It never writes sysfs, forces zero, or restores a presumed value.

Source review confirms OSM advertises per-policy governor attributes, and `get_governor_parent_kobj()` places the `schedutil` group beneath each policy kobject. `up_rate_limit_us` and `down_rate_limit_us` are RW attributes; tracked kernel source contains their stores but no Android userspace writer was found in the searched repository paths. ROM services outside this tree may override them. `sugov_tunables_restore()` may restore cached values after governor restart. Actual runtime values must therefore be captured and used as the experiment state record.

Validation: script `sh -n` and mock policy/global layout tests passed, including before/during/after TSV rows, not-active governor, missing fields, simulated permission denial, traversal and pseudo-filesystem output guards. Workflow selection still has three mutually exclusive variants and validates their effective config; matched comparison instructions now require the same full source SHA, release flavor/generation, toolchain provenance, and per-run artifact comparison. No source rate-limit behavior changed, no build or physical measurement was performed. Next: publish the worktree, run matched Actions builds, then capture baseline/CPU-001/CPU-002 tunables on vayu before proceeding to performance interpretation.



## Current execution checkpoint — 2026-11-07

This checkpoint adds no kernel tuning beyond the already documented opt-in CPU-001/CPU-002 experiments. It adds the read-only schedutil capture utility and matched-build/runtime-capture instructions. CPU-001/CPU-002 are **IMPLEMENTED** and their three Kconfig variants are **STATICALLY VALIDATED**; they are **NOT BUILT**, **NOT DEVICE VALIDATED**, **NOT MEASURED**, and **NOT ACCEPTED**. No subsystem performance changes were accepted.

Workflow YAML and embedded Bash syntax, `sh -n` for both collectors, local baseline/CPU-001/CPU-002 `olddefconfig` resolution, mock collector cases, and `git diff --check` passed. There is no compiler/linker/gh/ADB/fastboot in this environment; no Actions run was dispatched and no physical Poco X3 Pro was available. Therefore build, boot, performance, thermal, energy, stability, and compatibility results remain unavailable.

M3 is the next incomplete milestone. M4–M6 have source research but remain measurement-gated; M7–M11 cannot be accepted without independently validated candidates and physical evidence. The release-candidate decision is **NOT PREPARED**; see `RELEASE_CANDIDATE_REPORT.md`. Current branch is `experiment/m0-m1-reproducible-baseline`, HEAD `1d7baee8d8363b1a1369bd1b3e654e30d5d5cc87`, with uncommitted changes. No artifact location exists.


## M4–M6 source engineering checkpoint — 2026-11-07

M4 GPU review confirmed `kgsl_gpubusy`, `kgsl_pwrlevel`, `kgsl_buslevel`, and `kgsl_pwrstats` trace events already exist. With no frame-correlated device trace and secure TZ target selection, no KGSL policy change is justified. M5 adds MEM-002: Kconfig-off-by-default, workflow-selectable LZ4HC initial compressor; ordinary builds keep LZ4. The compressor implementation and runtime tunables remain unchanged. Baseline and LZ4HC `olddefconfig` outputs passed expected symbol checks. M6 source review found CPU/GPU cooling and thermal interactions, but no measured device state; no thermal, power, charging, or frequency safety control was modified.

MEM-002 is **IMPLEMENTED, STATICALLY VALIDATED, NOT BUILT, NOT DEVICE VALIDATED, NOT MEASURED, NOT ACCEPTED**. CPU-001/002 remain in the same validation state. No accepted performance optimization exists. M3 is still current; M5 has an experiment prepared but cannot be evaluated before a hosted build and rooted vayu run. M7–M11 remain pending. See `MEM_EXPERIMENT_MEM-002.md` and `RELEASE_CANDIDATE_REPORT.md`.


## Toolchain upgrade checkpoint — 2026-11-07

Added an isolated `clang-r614150` workflow option while preserving `clang-r547379` as the default. Official AOSP sources identify r614150 / LLVM 23.0.1 and the exact update commit; the workflow is prepared to acquire from the pinned archive and capture archive SHA, acquisition timestamp, version output, toolchain identity and artifacts. No local archive was obtained: VPS DNS resolution for `android.googlesource.com` failed. The host also lacks Clang/LLD and ARM cross compilers, so neither matched build ran. There are no images, checksums or ZIP artifacts, and no toolchain compatibility conclusion for Linux 4.14 can be made. See `TOOLCHAIN_R614150_REVIEW.md` and `TOOLCHAIN_BUILD_COMPARISON.md`.

M3/M4/M5 changes and reports remain preserved in the dirty worktree. No production source, device, thermal/charging control, commit, push, or Actions dispatch was changed/performed. The exact next requirement is DNS/network access plus the missing compilers/dependencies (or a successful authorized Actions run), then matched builds from the same full reviewed source state.


## VPS build attempt checkpoint — 2026-11-07

No kernel build could start. The execution sandbox denies network socket creation (`Operation not permitted`), while system DNS lookups fail for AOSP and GitHub. Resolver state points to systemd stub/8.8.8.8, but host systemd/netlink inspection is also denied; no networking changes were made. The AOSP archive was not downloaded and no Clang/LLD/cross compiler is installed. Required build packages are missing and could not be installed.

Offline work completed: generated and saved an effective vayu Xen+3 baseline config with ThinLTO/performance enabled and CPU/MEM experiments off. Config SHA: `7aef5933f1e0cfd82fd264573dbdf5ac5d9f508075c46e67e71db4e0964f59dc`. The old `build.sh` was intentionally not run because it executes `rm -rf out` and deletes AnyKernel ZIPs, violating workspace-preservation requirements. No AnyKernel3 packaging source is available in the checkout. There is no Image, ZIP, Image SHA, ZIP SHA, or Termux download path. Full details and next actions are in `VPS_BUILD_R614150_REPORT.md`.


## GitHub Actions publication checkpoint — 2026-11-07

The Lab origin was verified as `git@github.com:Lvyana-ren/Xen-Kernel-Lab.git`; the GitHub API confirms push/admin permission and the experiment branch at base SHA `1d7baee8d8363b1a1369bd1b3e654e30d5d5cc87`. The workflow is tracked and not ignored. Before publication audit, no staged files, artifact binaries, or secret-pattern matches were found. The workflow artifact upload was corrected to success-only and artifacts are uniquely named by vayu/toolchain/experiment/run.

No Actions run has been dispatched yet. The connected GitHub tools expose repository/ref mutation and artifact retrieval, but no workflow-dispatch operation; direct REST cannot be reached because the execution sandbox denies network sockets. No run URL, build result, or artifact exists. `GITHUB_ACTIONS_BUILD_REPORT.md` records exact baseline and r614150 dispatch parameters and remaining gates.

## Post-publication correction — 2026-11-07

The Lab experiment branch was published as `75e6994142f3896f55146ca8019ad91a978cdf25` with message `lab: prepare GitHub Actions kernel experiments`, parent `1d7baee8d8363b1a1369bd1b3e654e30d5d5cc87`. Remote branch verification succeeded. This supersedes earlier statements in this report that publication had not occurred. The local `.git/index` is read-only, so the connected GitHub Git-data API was used to publish without altering local Git metadata. The post-push Actions query returned zero runs; no dispatch-capable tool is available and direct network socket creation is blocked. No kernel build, artifact, device test, or performance result exists. The exact manual dispatch inputs are in `GITHUB_ACTIONS_BUILD_REPORT.md`.
