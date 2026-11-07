# Optimization candidate matrix

Evidence classes: **VERIFIED** means source/config fact; **HYPOTHESIS** means a possible limitation with no device evidence; **BLOCKED** means needed measurement/tool is unavailable.

| Priority | Area / candidate | Evidence today | Potential benefit | Cost/risk | Required test before patch |
|---|---|---|---|---|---|
| 1 | WALT/schedutil wake and ramp behavior | VERIFIED coupling in `walt.c`, `fair.c`, `cpufreq_schedutil.c`; no latency traces. | Lower wake-to-run/frame start latency if ramp delay is evidenced. | Aggressive response can increase frequency churn, energy and thermal saturation. | Scheduler wake/switch and CPU frequency trace correlated to UI markers; p50/p95/p99 and energy. |
| 2 | SchedTune group boost and task placement | SchedTune compiled; runtime mount/userspace assignment unknown. | Reduce frame-thread placement misses or extra migrations if measured. | Higher boost can raise power, heat and background interference. | Read groups/membership safely; trace task placement/migrations and frame timing. |
| 3 | Core_ctl thresholds/hysteresis | WALT invokes core control; configured policy values unknown. | Improve burst core availability or reduce needless online cores. | Hotplug/isolation latency, suspend/workqueue/IRQ regressions. | Core state timeline + WALT demand and workload, plus idle drain and suspend tests. |
| 4 | CPU idle state selection | Qualcomm LPM/menu code present; registered states/residency unknown. | Improve energy or tail latency if an observed prediction error exists. | Shallower states increase idle energy; deeper states may worsen wake tails. | CPU idle trace/residency paired with wake latency, energy and suspend success. |
| 5 | KGSL Adreno TZ/devfreq response | KGSL and governor support configured; device runtime state absent. | Improve frame-time stability if GPU frequency response is limiting. | Raising levels increases heat/power and may steal thermal budget from CPU. | GPU busy/frequency/power-level trace, frame-time capture and thermal state. |
| 6 | ZRAM compressor/size/reclaim policy | LZ4 source default; runtime setup unknown. | Better memory pressure behavior if compression CPU or ratio is measured as limiting. | Different algorithm changes CPU use, memory footprint and latency; swap can affect I/O. | Capture actual algorithm/size/mm_stats, PSI, vmstat and controlled pressure tests. |
| 7 | Storage scheduler/queue attributes | Several schedulers compiled; active UFS queue unknown. | Reduce I/O tail latency if queue contention is shown to affect app/frame workloads. | More scheduling overhead or worse throughput/fairness. | Device type, queue scheduler, diskstats and workload latency histograms. |
| 8 | Thermal/CPU-GPU budget coordination | LMH, thermal and cooling paths are integrated; live ROM control unknown. | Preserve sustained frame pacing through better balancing only if control conflict exists. | Safety risk; no thermal trips/limits may be weakened. | Long sustained mixed workload with zones, cooling states, frequency and energy. |
| 9 | Background service interference | Android framework/cgroups control is ROM-specific and unobserved. | More consistent foreground response if interference is measured. | Starvation, delayed services, battery costs. | Reproducible background load, cgroup placement and scheduler traces. |

**CPU-001 and CPU-002 are implemented as opt-in experiment builds, not accepted optimizations.** A read-only collector now records actual governor tunables, policy membership and frequency limits across run phases, so userspace/cached overrides can be identified. GPU source review confirms a TrustZone-controlled target decision after accumulated busy/total-time gating, but provides no safe, evidence-backed threshold change. ZRAM, block queue and thermal behavior likewise lack runtime workload evidence. The ordering is by evidence value and testability, not expected speedup. Compare frame-time tails, responsiveness, energy, temperature and sustained behavior.


## Current decision checkpoint

CPU-001 and CPU-002 remain opt-in, statically configuration-checked candidates only. No candidate has been built, measured, accepted, or rejected by runtime evidence. GPU, memory/storage, and thermal/power candidates remain deferred because source review alone did not establish a bottleneck and no safe configuration change is justified. Do not integrate candidates together before isolated build and device evaluation.


| 10 | ZRAM compressor comparison: LZ4 baseline vs opt-in LZ4HC default (MEM-002) | **VERIFIED:** source has LZ4HC backend behind `CONFIG_CRYPTO_LZ4HC`; the experiment selects it only when enabled. | Potentially lower compressed footprint under suitable page corpus. | More compression CPU work/energy and longer write path; userspace may override. | Same-SHA builds; rooted device confirms actual algorithm; randomized pressure runs recording mm_stat, PSI, reclaim, app latency, energy and thermal trajectories. |

MEM-002 is **IMPLEMENTED / STATICALLY VALIDATED / NOT BUILT / NOT DEVICE VALIDATED / NOT MEASURED / NOT ACCEPTED**.
