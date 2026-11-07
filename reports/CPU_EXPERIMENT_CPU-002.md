# CPU-002: remove only schedutil's upward rate limit

## Status

Implemented as a separate opt-in build variant. The baseline, CPU-002-only and CPU-001-only configurations were checked with `olddefconfig` and resolve mutually exclusively; no kernel build or device measurement has occurred. This is an experiment, not an accepted optimization.

## Hypothesis

The CPU-001 source trace shows separate up/down gates in `sugov_up_down_rate_limit()`. If a material `cpufreq_policy_transition_delay_us()` value delays workload ramp-up, removing only `up_rate_limit_us` may permit earlier increases while preserving downward pacing. This isolates ramp-up from frequency-release behavior and is a smaller behavioral change than CPU-001.

The source fallback for this delay is 1000 microseconds when no policy-specific delay or CPU transition latency is set. The vayu OSM driver enables fast switch but does not set transition latency in its policy-init function. This provides a concrete code-level reason to test the gate, while runtime policy values and any userspace governor writes remain unverified.

The hypothesis remains conditional: the actual vayu policy transition delay may be zero or negligible, and a faster target request may not yield an earlier hardware frequency transition or visible latency improvement. More up-frequency requests can increase energy and thermal load.

## Exact changes

- `drivers/cpufreq/Kconfig`: adds default-off `CONFIG_XEN_EXPERIMENT_SUGOV_NO_UP_RATE_LIMIT`, mutually exclusive with CPU-001's both-directions option.
- `kernel/sched/cpufreq_schedutil.c:sugov_init()`: initializes up limit to zero, retains `cpufreq_policy_transition_delay_us(policy)` for the down limit.
- `.github/workflows/build-kernel.yml`: adds `cpu_experiment=sugov_no_up_rate_limit`, explicitly sets both experiment symbols for each variant, and checks mutual exclusion/effective config after `olddefconfig`.

The existing `baseline` workflow choice remains default. Neither experiment modifies WALT accounting, task placement, cpufreq policy min/max, hardware frequency tables, core control, idle, thermal, charging, GPU or memory behavior.

## Evaluation

Build baseline, CPU-002 and CPU-001 from the same source/toolchain. On vayu, verify after ROM startup that `up_rate_limit_us=0` and `down_rate_limit_us` matches the platform default for CPU-002, and record the live values for all variants. Use matched workload runs and capture scheduler wake/update events, `cpu_frequency`, policy transition delay, frequency residency/request counts, wake latency, frame times, current/energy and thermal/cooling state. Require repeated runs and sustained tests. Reject if latency/frame tails do not improve consistently or if energy, thermal headroom, sustained performance, background fairness, boot, suspend or stability regresses.

## Runtime tunable verification and capture

Use `/sys/devices/system/cpu/cpufreq/policyN/scaling_governor` to verify schedutil is active. For the OSM per-policy layout, read `/sys/devices/system/cpu/cpufreq/policyN/schedutil/up_rate_limit_us` and `down_rate_limit_us`. Read CPU policy masks from `related_cpus` and `affected_cpus`; current frequency from `scaling_cur_freq` and, if exposed, `cpuinfo_cur_freq`; limits from `scaling_min_freq`, `scaling_max_freq`, `cpuinfo_min_freq`, `cpuinfo_max_freq`, and `scaling_available_frequencies`. A global `/sys/devices/system/cpu/cpufreq/schedutil/` directory may be used on other driver layouts. These paths are source-derived; verify existence and governor on the actual device.

Capture with the same read-only script and command procedure in [CPU-001 runtime tunable verification](CPU_EXPERIMENT_CPU-001.md#runtime-tunable-verification-and-capture), using run label `cpu002` and a separate TSV output. Capture `before`, repeated `during`, and `after` states. Expect the initial up limit to be zero and down limit to retain the driver's initial transition delay, but record the values actually observed. Android userspace may write the RW sysfs attributes, and `sugov_tunables_restore()` may restore in-kernel cached values after a governor restart; do not force values to match the expected experiment.

## Rollback

Build with `cpu_experiment=baseline` to retain the original defaults. Revert the CPU-002 Kconfig, schedutil, workflow and report changes to remove this variant. Do not promote without build plus device evidence.
