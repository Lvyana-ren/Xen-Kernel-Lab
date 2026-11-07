# CPU baseline capture checklist

Use this checklist with [DEVICE_BASELINE_GUIDE.md](DEVICE_BASELINE_GUIDE.md) and [RUNTIME_BASELINE.md](RUNTIME_BASELINE.md). The collector is read-only and captures point snapshots. It does not establish a bottleneck by itself. Record missing and permission-denied interfaces explicitly; never substitute zero.

## Point data available from the collector

- [ ] **Identity/configuration:** device codename, ROM fingerprint, Android release, kernel release/version, collection timestamp, root UID and SELinux state. Preserve `metadata.txt` and `manifest.tsv` with every run.
- [ ] **CPU topology:** `/sys/devices/system/cpu/{possible,present,online,isolated,nohz_full}` and per-CPU `online` nodes where exposed. Record online, isolated and nohz_full masks separately, plus any offline CPUs. An absent mask is not equivalent to an empty mask.
- [ ] **Runtime cpufreq driver and policies:** policy `scaling_driver`, `affected_cpus`, `related_cpus`, current governor, available governors, current frequency, and transition latency where present. Do not infer one policy per CPU; preserve masks as reported.
- [ ] **Frequency range:** available frequencies, `cpuinfo_min_freq`, `cpuinfo_max_freq`, `scaling_min_freq`, `scaling_max_freq`, and `stats/time_in_state` where present. These values are requested by the collector. Compare exact units and policy masks before aggregating.
- [ ] **CPU idle:** per-CPU state name/description, latency, power, usage count, cumulative time, and disable state where present. Two snapshots around a defined interval can provide residency deltas if counters are cumulative and have not reset.
- [ ] **WALT-related scheduler state:** the collector requests `/proc/sys/kernel/sched_*`. Inspect returned names and values. A source Kconfig option or an absent sysctl alone does not prove the runtime scheduler mode or WALT state.
- [ ] **Schedtune scalar policy:** the collector now checks root and one-level child files for schedtune boost/prefer_idle and related scalar attributes under `/dev/stune`, `/sys/fs/cgroup/stune`, and `/sys/fs/cgroup/schedtune`. Review manifest path statuses. It does not collect task lists or per-process membership.
- [ ] **Core control:** collector requests `/sys/devices/system/cpu/hyp_core_ctl/{enable,status}` and debugfs reserve CPUs, plus per-CPU `core_ctl/*` nodes. Record what is present and permission status. Determine active CPU count from the online mask at each timestamp.
- [ ] **Thermal/cooling:** thermal zone type/temp/mode/policy/trip metadata and cooling-device type/current/max state. Record ambient temperature separately; device thermal readings are not ambient measurements.
- [ ] **Supporting context:** battery temp/current/voltage/charge/status, memory pressure, ZRAM, dmesg, and suspend/wakeup snapshots. Keep these aligned with workload start/end times.

## Manual runtime supplement

The following are not guaranteed in the collector output. Read them manually only after checking whether the path exists and whether the rooted shell can read it. Save raw output and note command, timestamp, exit status, and permission errors.

### Schedutil experiment capture

For each baseline/CPU-001/CPU-002 boot, use `scripts/xen-baseline/collect-schedutil.sh` to append `before`, repeated `during`, and `after` snapshots. It records policy masks, active governor, instantaneous frequency, available/min/max limits and the `up_rate_limit_us`/`down_rate_limit_us` values from the active governor's sysfs group. The OSM vayu path is under `policyN/schedutil/`; verify runtime path existence. A missing or unreadable path remains unavailable/permission-denied in the TSV and is never represented as zero. Do not write either tunable. See the experiment reports for the exact ADB invocation.

- [ ] **Isolation and scheduler domains:** the collector requests isolated and nohz_full masks when present. Also inspect boot command line for isolcpus/nohz_full/rcu_nocbs and record cpuset CPU masks only for named system groups relevant to the test. Avoid copying unrelated process lists.
- [ ] **Schedtune groups:** identify the actual mounted controller and group files; collector only covers named scalar files at root and one child level. Record deeper relevant group values and controller mount path manually without task lists or writes. Do not treat a missing controller as a zero boost.
- [ ] **Runtime driver confirmation:** preserve `scaling_driver` output for every policy and cross-check with kernel config/source and boot logs. Configured driver support does not prove which driver registered at runtime.
- [ ] **Core_ctl detail:** capture all readable attributes under the specific `core_ctl` sysfs group, including min/max CPUs, busy thresholds, offline delay, and policy fields if present. Determine whether `hyp_core_ctl`, regular core_ctl, or both are active from actual nodes/logs, not source alone.
- [ ] **Frequency residency by scenario:** capture policy `time_in_state` immediately before and after idle, interactive, and gaming windows. Calculate per-frequency deltas over elapsed time and retain the raw counters. `scaling_cur_freq` is only a sample, not residency. Confirm counter units/semantics before comparing.
- [ ] **Thermal response:** capture zone temperatures and cooling states before, during, and after sustained load at a sampling rate justified by the question. Prefer light periodic sampling; note that polling itself adds some overhead.

## Data requiring trace instrumentation or external measurement

- [ ] **Wakeup latency distributions:** targeted ftrace/perfetto trace events such as scheduler wakeup/waking/switch, IRQ/softirq and CPU idle entry/exit, correlated to a defined userspace marker. A snapshot cannot measure sub-millisecond wakeup latency. Keep trace duration short and compare traced/untraced behavior.
- [ ] **Frequency transition latency:** capture `power:cpu_frequency`/available power events or platform tracepoints while triggering controlled workload transitions; record transition timestamps and requested versus actual frequency where the events expose both. Static `cpuinfo_transition_latency` is a declared estimate, not a measured transition distribution.
- [ ] **WALT load/utilization evolution:** use available WALT trace events or instrumented scheduler traces and task/cgroup markers. Readable sched sysctls show controls, not per-task load history or placement decisions.
- [ ] **Core_ctl decisions:** trace available `hyp_core_ctl` events/status or targeted scheduler/CPU hotplug events to correlate policy decisions with online-mask changes. Avoid broad debug logging.
- [ ] **Gaming frame pacing:** collect per-frame timestamps with a consistent SurfaceFlinger/Perfetto or game-supported frame-time source. Report frame-time percentiles, missed/deadline frames and a defined 1% low method, alongside CPU/GPU/thermal context. Benchmark scores alone are insufficient.
- [ ] **Battery/energy:** use repeatable charge/energy counters and long enough controlled runs. Instantaneous current is noisy and can be sign-convention/vendor dependent; retain raw samples and characterize the measurement source.

## Minimum scenario record

For idle, interactive, and gaming scenarios, record workload/app/version, exact duration and steps, starting/ending battery and temperatures, display/network state, online CPU mask, cpufreq policy limits/governors, thermal/cooling state, and pre/post snapshot paths. Use at least five repetitions per condition and report all raw runs, median, and spread (IQR or MAD). Randomize comparison order and restore the same cooldown/starting conditions. Do not change tuning, thermal trips, charging limits, or CPU/GPU clocks.

## Status

No physical vayu data or traces are present. Collector availability, WALT/schedtune runtime exposure, policy driver, residency-counter semantics, and tracepoint availability all require device verification.
