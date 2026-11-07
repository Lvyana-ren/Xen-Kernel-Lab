# GPU and Adreno/KGSL source research

## Static architecture

`vayu_defconfig` enables `CONFIG_QCOM_KGSL`, `CONFIG_QCOM_KGSL_IOMMU`, `CONFIG_DEVFREQ_GOV_QCOM_ADRENO_TZ`, and sets `CONFIG_QCOM_ADRENO_DEFAULT_GOVERNOR="msm-adreno-tz"`. The default string is a compiled default, not proof the running ROM uses it. Sources include `drivers/gpu/msm/Kconfig`, `kgsl_pwrscale.c`, `kgsl_pwrctrl.c`, `kgsl_device.c`, `adreno.c`, and `drivers/devfreq/governor_msm_adreno_tz.c`.

The KGSL pwrscale path gathers device busy/total time and exposes devfreq status to the governor. `governor_msm_adreno_tz.c` initializes governor policy and computes target frequency from load/status plus device-specific constraints. `kgsl_pwrctrl.c` owns GPU power levels, clock/bus votes, thermal power-level/constraint interfaces and gpubusy reporting. GPU frequency and bus votes are coupled: increasing the GPU state can request memory/bus bandwidth and increase SoC thermal load. Exact runtime Adreno revision, firmware/GPU bin, frequencies and governor must be read from the device.

## Safe measurement interfaces

The M1 collector requests named KGSL and devfreq files such as available/current frequency, gpubusy/utilization, governor, power level and transition statistics where exposed. Missing nodes remain explicit. For frame pacing, use a short Perfetto/game-supported frame timeline and match CPU/GPU/thermal snapshots; static `gpubusy` samples are not per-frame latency data. Never modify `max_gpuclk`, pwrlevel limits, bus votes, idle timer or thermal constraints during baseline collection.

## Optimization status

No GPU tuning is justified yet. A low utilization sample does not prove a GPU bottleneck; frame time can be CPU, memory, compositor, display or thermal limited. A candidate requires correlated GPU utilization/frequency, CPU scheduling and per-frame data plus sustained temperatures and energy. No GPU clocks, governor or thermal behavior was changed. All expected performance and energy effects remain **DEVICE VALIDATION REQUIRED**.

## Follow-up source review — 2026-11-07

`drivers/devfreq/governor_msm_adreno_tz.c:tz_get_target_freq()` accumulates `stats.total_time` and `stats.busy_time`, returns without policy work until accumulated total time reaches `FLOOR` (5 ms) and busy time reaches `MIN_BUSY` (1 ms), and has a busy-burst path above `CEILING` (50 ms). Otherwise it delegates the target-level decision to `__secure_tz_update_entry3()`. `compute_work_load()` separately accumulates normalized GPU busy statistics. KGSL then constrains/applies requested power levels in `drivers/gpu/msm/kgsl_pwrctrl.c`, including thermal max/min bounds.

These constants and secure call structure are verified source facts, not evidence of incorrect vayu frame pacing. Changing the thresholds could alter sample cadence, request load, energy and temperature, while ordinary target behavior is partly inside TrustZone. **GPU-001 remains deferred** until device capture correlates per-frame deadlines, `gpubusy`, GPU frequency/power level, CPU scheduling, thermal caps and sustained energy. Do not edit `FLOOR`, `MIN_BUSY`, `CEILING`, pwrlevels or thermal limits without those results.


## M4 implementation decision

The existing KGSL trace events in `drivers/gpu/msm/kgsl_trace.h` include `kgsl_gpubusy` (busy and elapsed time), `kgsl_pwrlevel`, `kgsl_buslevel`, and `kgsl_pwrstats` (total, busy, RAM time/wait, context count). The governor `tz_get_target_freq()` relies on device status and secure TZ policy. Because the tree already provides focused tracepoints and no device trace identifies a governor defect, no GPU frequency or threshold patch was added. GPU-001 remains a trace-driven candidate; enable only the needed trace events during a bounded, matched run, correlate with frame timelines/CPU/thermal state, and avoid changing TrustZone inputs or KGSL limits. No runtime measurement is available here.
