# CPU-001: schedutil rate-limit A/B build

## Status

**Implemented as an opt-in build experiment; config verified, but not built, booted, or measured.** It is not an accepted optimization. The default `baseline` workflow choice leaves vayu configuration and schedutil behavior unchanged.

## Hypothesis

`kernel/sched/cpufreq_schedutil.c:sugov_init()` initializes both `up_rate_limit_us` and `down_rate_limit_us` from `cpufreq_policy_transition_delay_us(policy)`. `sugov_start()` converts them to nanoseconds. In `sugov_should_update_freq()`, `min_rate_limit_ns` is the minimum of those delays; with both zero this gate is satisfied on each call. In `sugov_up_down_rate_limit()`, an increase/decrease is rejected only when elapsed time is less than its corresponding delay; with both zero, neither directional check rejects a nonnegative elapsed time. `sugov_update_commit()` still skips an unchanged target, and frequency resolution, policy limits, driver behavior, and thermal constraints remain in force.

The fallback implementation in `drivers/cpufreq/cpufreq.c:cpufreq_policy_transition_delay_us()` uses a defined `transition_delay_us` if present; otherwise it derives a value from `cpuinfo.transition_latency`, capped at 10 ms after applying `LATENCY_MULTIPLIER`. If both are zero, it returns `LATENCY_MULTIPLIER`, which is 1000 microseconds in `include/linux/cpufreq.h`. The OSM CPUFreq driver marks `fast_switch_possible` but does not assign transition latency in `osm_cpufreq_cpu_init()`. This suggests the source fallback may be 1 ms for OSM if no other code populates policy delay/latency; the exact runtime policy value still must be read on vayu.

Thus the compile-time option does remove schedutil's software rate-limit gates when the zero values are active. It does **not** guarantee a hardware transition for every scheduler update. Governor tunables remain writable, and `sugov_tunables_restore()` can restore cached tunables after governor restart; verify live values after boot and userspace initialization.

This is a **strong source-based hypothesis, not a verified bottleneck**. The code path confirms the intended gating change. No vayu transition delay, live governor values, wake trace, frame timing, power or thermal measurements are available. More target-frequency changes are possible; actual hardware transition count, instability, energy and heat cannot be determined from source inspection.

## Implementation

- `drivers/cpufreq/Kconfig`: adds `CONFIG_XEN_EXPERIMENT_SUGOV_NO_RATE_LIMIT`, depending on schedutil and defaulting to `n`.
- `kernel/sched/cpufreq_schedutil.c`: under that option, initializes schedutil's up/down rate limits to zero. Normal builds retain the existing transition-delay defaults. Existing runtime governor tunables remain available and may override the initial values.
- `.github/workflows/build-kernel.yml`: adds explicit `cpu_experiment` choices `baseline` and `sugov_no_rate_limit`; baseline is default. It validates the final symbol after `olddefconfig` and captures the selected experiment in artifacts.

The experiment does not alter WALT, placement, schedtune, core_ctl, CPU frequency tables/limits, idle states, GPU, thermal or charging behavior. It does affect the frequency governor's initial pacing and is therefore a kernel behavior change in the opt-in variant.

## Evaluation procedure

1. Build the same published source SHA/toolchain three times, selecting `baseline`, `sugov_no_up_rate_limit`, and `sugov_no_rate_limit`; retain each workflow artifact and verify `kernel.config`, release, image checksum and experiment metadata.
2. On the rooted vayu device, collect active policy masks, `scaling_driver`, transition delay, governor tunables, min/max limits and thermal/cooling state after boot and after the ROM's boot-time services settle. Confirm the experiment's tunables remain zero; note any userspace rewrite.
3. Use identical ROM, app version, workload, display, charge band, ambient temperature and cooldown. Randomize at least five matched runs per variant.
4. Capture a targeted low-overhead trace of `sched_waking`, `sched_wakeup`, `sched_switch`, `cpu_frequency` and idle events, synchronized with an interactive marker. For gaming, capture frame times and GPU busy/frequency alongside CPU data.
5. Report wake-to-run and wake-to-frequency distributions, frame-time p50/p95/p99 and 1% low with stated convention, frequency residency/request counts, current/energy, temperatures, cooling state and sustained throughput. Compare medians and spread, not just peak score.
6. Check boot stability, suspend/resume, thermal behavior, idle drain and background workload fairness. Reject if response/frame timing does not improve consistently or if energy, temperature, sustained performance or stability regresses materially.

## Runtime tunable verification and capture

The vayu OSM driver sets `CPUFREQ_HAVE_GOVERNOR_PER_POLICY`; `get_governor_parent_kobj()` therefore parents schedutil's tunable group under each CPUFreq policy kobject. For a running `policyN` whose governor is schedutil, inspect:

```sh
/sys/devices/system/cpu/cpufreq/policyN/scaling_governor
/sys/devices/system/cpu/cpufreq/policyN/schedutil/up_rate_limit_us
/sys/devices/system/cpu/cpufreq/policyN/schedutil/down_rate_limit_us
```

Read policy membership, current governor/frequency, and limits with this rooted ADB shell command. It reads paths only when they exist; it does not write a tunable:

```sh
adb shell su -c '
for p in /sys/devices/system/cpu/cpufreq/policy[0-9]*; do
  [ -d "$p" ] || continue
  echo "[$p]"
  for a in related_cpus affected_cpus scaling_driver scaling_governor \
      scaling_cur_freq cpuinfo_cur_freq scaling_min_freq scaling_max_freq \
      scaling_available_frequencies cpuinfo_min_freq cpuinfo_max_freq \
      cpuinfo_transition_latency scaling_transition_latency; do
    [ -r "$p/$a" ] && { printf "%s=" "$a"; cat "$p/$a"; } || echo "$a=unavailable"
  done
  if [ "$(cat "$p/scaling_governor" 2>/dev/null)" = schedutil ]; then
    t="$p/schedutil"
    [ -d "$t" ] || t=/sys/devices/system/cpu/cpufreq/schedutil
    for a in up_rate_limit_us down_rate_limit_us; do
      [ -r "$t/$a" ] && { printf "%s=" "$a"; cat "$t/$a"; } || echo "$a=unavailable"
    done
  fi
done'
```

The source-defined OSM location is per-policy as above. The global `.../cpufreq/schedutil/` fallback is for kernels/drivers using global governor tunables. Confirm the discovered path on the running device; do not assume a node exists. The sysfs attributes are read/write in the kernel, so privileged Android init/performance services can overwrite them if device permissions allow. This repository contains no Android userspace write to these two attributes in tracked sources; the actual ROM's services remain unknown. `sugov_tunables_restore()` can also restore values cached in kernel memory after a governor restart. The cache is in-kernel memory and does not itself persist across reboot. Therefore record, do not correct, values that differ from the experiment's initialization settings.

Initialization detail: `sugov_tunables_restore()` copies the cached tunable values and calls `update_min_rate_limit_ns()`, but this runs in `sugov_init()` before `sugov_start()` loads the per-policy nanosecond delays. On a new policy, `sugov_start()` loads those directional delays but does not recalculate `min_rate_limit_ns`. That internal minimum gate can consequently remain zero until a runtime tunable write. This is existing baseline behavior: the minimum gate only avoids recalculating a target; directional commit rejection still uses `up_rate_delay_ns` and `down_rate_delay_ns`. It does not change the sysfs values to be captured or the experiment's directional comparisons.

Capture timestamped values before, during and after the workload using the read-only script. The output directory must already exist; the script appends to one regular TSV file and refuses relative, traversing, symlinked, or pseudo-filesystem output paths:

```sh
adb push scripts/xen-baseline/collect-schedutil.sh /data/local/tmp/collect-schedutil.sh
adb shell su -c 'chmod 0755 /data/local/tmp/collect-schedutil.sh'
adb shell su -c '/data/local/tmp/collect-schedutil.sh baseline before /sdcard/cpu001-schedutil.tsv'
adb shell su -c '/data/local/tmp/collect-schedutil.sh baseline during /sdcard/cpu001-schedutil.tsv'
adb shell su -c '/data/local/tmp/collect-schedutil.sh baseline after /sdcard/cpu001-schedutil.tsv'
adb pull /sdcard/cpu001-schedutil.tsv ./cpu001-schedutil.tsv
```

For CPU-001, use `cpu001` as the run label; for the matched default build use `baseline`. Repeat `during` captures at defined workload points (for example start, peak and end). Store CPU-002 in its own file with `cpu002` as label. Do not write sysfs values to force zero or restore a presumed default. The script records policies, policy CPU masks, governor, instantaneous frequencies, available/current limits, transition-latency metadata, both tunables, capture phase, device and kernel release. Missing and permission-denied fields are explicit. Current-frequency samples are instantaneous readings, not residency measurements.

## Rollback and decision gate

Select `cpu_experiment=baseline` to build the existing behavior. The source option defaults off, so normal defconfig builds do not enable it. To remove the experiment completely, revert the three implementation/workflow file changes and the corresponding report entry. Do not promote this variant without a successful build and physical vayu results reviewed by the technical lead.

## Validation state

- Source control flow reviewed: **done**.
- Workflow/config integration review: **done**.
- YAML and embedded shell static validation: **passed** (PyYAML parse, workflow choice assertions, `bash -n` on all embedded Bash run blocks).
- Kconfig `olddefconfig` validation: **passed** in `/tmp/xen-cpu001-config`; experiment symbol enabled in the experiment config and unset in the baseline config, with schedutil still enabled in both.
- Runtime sysfs tunable collection: script added; mock policy/global paths and before/during/after output validated; physical values pending.
- Kernel build: **not run**.
- Physical device and performance/energy/thermal evaluation: **not run; requires rooted Poco X3 Pro**.
