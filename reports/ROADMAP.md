# Xen-Kernel Lab optimization roadmap

**State snapshot:** 2026-11-07. Branch `experiment/m0-m1-reproducible-baseline`; initial HEAD `1d7baee8d8363b1a1369bd1b3e654e30d5d5cc87`. The kernel source baseline is Linux 4.14.357 with vayu/SM8150 support. This worktree contains prior documentation/collector updates and the new uncommitted, opt-in CPU-001 source/workflow experiment. No performance effect has been built or measured.

## Milestones and gates

| Milestone | Objective | Current state | Exit evidence |
|---|---|---|---|
| M0 | Reproducible CI inputs, source/patch/config/toolchain/artifact provenance | Workflow and patch handling are implemented and committed. No hosted run is visible for this branch. Dependency versions are recorded, but runner, apt and action refs remain mutable. | Successful manual workflow run; inspect actual config, patch list/diff, build log, release and artifact checksums. A second same-input run is needed to assess reproducibility. |
| M1 | Device/host baseline collection | Read-only collector and protocol exist; collector now includes topology, schedtune scalars, block queue state and counters. No rooted vayu capture exists. | At least one complete device snapshot plus idle, interactive, gaming, sustained, memory/I/O and suspend data with controlled repetitions. |
| M2 | Source trace CPU/scheduler and subsystem research | CPU report was prepared against parent source SHA `bf6ac124`; source code is unchanged in M0 commit. GPU, memory/storage, thermal/power and latency static reports are added in this roadmap cycle. | Code path/Kconfig/config/runtime interface trace reviewed and unknowns listed. Static completion does not imply runtime conclusions. |
| M3 | CPU experiments | CPU-001 both-limits-off and CPU-002 up-limit-only variants implemented; read-only active-tunable capture added. Source/config checks passed; no kernel build or physical measurement. | Build baseline and variants; collect tunables before/during/after; boot/device A/B with matched wake/frequency/frame/energy/thermal traces; accept/reject based on distributions and regression gates. |
| M4 | GPU experiments | KGSL/msm-adreno-tz source and existing KGSL tracepoints reviewed. No safe governor/clock change justified; no driver behavior changed. | Capture busy/power-level/bus-level/pwrstats events correlated to per-frame timing, CPU and thermal data before selecting a candidate. |
| M5 | Memory/ZRAM/storage experiments | MEM-002 opt-in LZ4HC initial-compressor comparison implemented; baseline remains LZ4. Baseline/experiment configs statically validated; no build/runtime data. | Matched build and vayu memory-pressure trials recording active compressor, mm_stat, PSI, CPU time, latency, energy and thermals. |
| M6 | Thermal and power experiments | Source/DTS/thermal interactions reviewed; no physical temperature/current timeline. Protections unchanged; no safety-policy patch justified. | Measure sustained CPU/GPU mixed load and energy with all zone/cooling state before any policy experiment. |
| M7 | Cross-subsystem validation | Not started. | Validate combinations of independently supported experiments under CPU/GPU/memory/I/O/thermal mixed workloads. |
| M8 | Interactive/gaming latency | Not started. | Timestamped touch-to-frame, scheduler wake and frame-time distributions with matched repetitions. |
| M9 | Efficiency and sustained workloads | Not started. | Energy/performance and thermal steady-state comparison for idle, screen-on, gaming and background workloads. |
| M10 | Final integration and release candidate | Not started. | Full build, device boot/stability/security review, regressions cleared, selected config and artifact provenance documented. |
| M11 | Physical acceptance and promotion gate | Added because hosted CI alone cannot prove vayu boot/runtime safety, and this environment has no Poco device or Android transport. | Technical lead/operator runs physical battery of tests and explicitly approves promotion. No production repository operation is authorized here. |

## Optimization discipline

No default-on optimization is supported by current evidence. CPU-001 is isolated behind an opt-in build configuration and leaves the baseline behavior unchanged; it is a falsifiable experiment, not an accepted optimization. Changing default frequencies, scheduler policy, GPU behavior, reclaim, thermal or charging controls remains unsupported without actual vayu workload measurements.

Do not declare a milestone complete merely because its static report exists. M0 has implementation evidence but hosted-run acceptance is pending. M1 and all performance milestones require physical-device evidence. If hardware remains unavailable, record them as externally blocked rather than infer results.

## Completion condition

The mission reaches its endpoint when M0 is verified by at least one successful hosted build and repeatability assessment, M1 and each selected optimization experiment have device evidence, M10 integration has no unresolved critical regression, and M11 technical lead promotion review is recorded. Until then, the project is **in progress / externally blocked**, not complete.


## Execution checkpoint — 2026-11-07

M3 remains the current active milestone. Local `vayu_defconfig`/`olddefconfig` matrix validation passed for baseline, CPU-001, and CPU-002; workflow YAML and embedded Bash syntax, both shell collectors, and `git diff --check` passed. No kernel compile, Actions run, device capture, benchmark, or performance measurement was performed. The source candidates remain unbuilt/unvalidated; no acceptance decision is supported. M4–M6 source research is complete for the reviewed code paths, but no device-supported experiment is justified. M7–M11 remain gated on M3 and device evidence. See `RELEASE_CANDIDATE_REPORT.md`: no release candidate exists.

The worktree is still uncommitted on `experiment/m0-m1-reproducible-baseline` at HEAD `1d7baee8d8363b1a1369bd1b3e654e30d5d5cc87`. Actions dispatch and publication are explicitly outside current authorization; CI and physical device access are unavailable. Next: operator publishes the reviewed branch, runs matched baseline/CPU-002/CPU-001 Actions builds on one full source SHA, then obtains rooted vayu baseline and A/B captures.


## Execution checkpoint — M3/M4/M5/M6 advancement

CPU source investigation found no additional CPU tuning justified without CPU-001/002 build and trace results. M4 review confirmed existing KGSL tracepoints cover busy, power-level, bus-level, and power statistics, so no governor/clock change was added. M5 now has MEM-002, an isolated opt-in LZ4HC initial-compressor comparison with LZ4 baseline preserved. Baseline and experimental Kconfig variants passed `olddefconfig`; workflow YAML, embedded Bash syntax, collectors and whitespace checks passed. M6 remains a safety-critical measurement gate; no thermal/power control changes. No compile, Actions dispatch, device test, or measurement occurred. M7–M11 still require earlier build and physical evidence.
