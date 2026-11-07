# Xen-Kernel CPU Deep Research — M2

**Scope:** source-level analysis of Xen-Kernel branch `experiment/m0-m1-reproducible-baseline`, based on source commit `bf6ac1247feda28293062995d445506b050aec8a`. Target is Poco X3 Pro (`vayu`, SM8150), kernel 4.14.357. This report is CPU-only. No kernel behavior or runtime setting was changed, and no device measurement or benchmark was performed.

**Current branch reconciliation (2026-11-07):** repository HEAD is `1d7baee8d8363b1a1369bd1b3e654e30d5d5cc87`. Diff from the report's source revision contains only CI workflow, patch-management and collector files; no scheduler, cpufreq, cpuidle, thermal, GPU, memory or platform C/DTS source changed. The source findings remain applicable, but all runtime status remains unknown.

**Evidence labels:** **VERIFIED** = present in this checkout/config or directly follows from code; **STRONG HYPOTHESIS** = source behavior makes a measurable effect plausible, but the actual workload/device effect is unmeasured; **WEAK HYPOTHESIS** = possible but source evidence is indirect; **DEVICE VALIDATION REQUIRED** = cannot determine deployed runtime state or outcome without vayu.

## 1. Executive summary

- **VERIFIED:** `vayu_defconfig` enables WALT (`CONFIG_SCHED_WALT`), SchedTune (`CONFIG_SCHED_TUNE`), scheduler core control (`CONFIG_SCHED_CORE_CTL`), CPUFreq with schedutil as default, frequency time statistics, CPU idle/menu, Qualcomm MSM power management, and Qualcomm OSM CPU clock support.
- **VERIFIED:** CPU placement is coupled to WALT task/runqueue demand, capacity-aware fair scheduling, SchedTune/per-task boost, cstate-aware wake placement, and scheduler core_ctl. The schedutil implementation consumes WALT metrics when enabled and uses scheduler update-util hooks; Qualcomm OSM advertises fast switching and derives frequency steps from hardware-programmed registers.
- **VERIFIED:** The SM8150 DTS describes eight CPUs in three CPU-map clusters: CPU0–3 have `capacity-dmips-mhz=1024`; CPU4–7 have `1740`. CPU7 is its own cluster and has a separate energy-cost phandle from CPU4–6. The DTS also supplies energy-cost data, `qcom,lmh-dcvs` links, and a `qcom,clk-cpu-osm` controller. Exact runtime CPUFreq policy masks/table and active idle states are not known from DTS source alone.
- **VERIFIED:** `CONFIG_QCOM_HYP_CORE_CTL` is enabled and depends on `OKL4_GUEST`; however no `qcom,hyp-core-ctl` compatible node was found in the checked-in vayu/SM8150 DTS files. The symbol therefore proves code availability, not driver probe or active CPU reservation on the phone.
- **No evidence-supported runtime bottleneck is established.** There are no target-device traces, residency counters, latency distributions, temperature series, or workloads. The best-supported next action is read-only baseline capture and scheduler/cpufreq tracing. No tuning change is recommended yet.

## 2. Current Xen CPU architecture

### Configuration and SoC map

| Area | Verified config/source | Runtime exposure to collect |
|---|---|---|
| Scheduler | `CONFIG_SCHED_WALT=y`, `CONFIG_SCHED_TUNE=y`, `CONFIG_SCHED_CORE_CTL=y` in `arch/arm64/configs/vayu_defconfig`; definitions in `init/Kconfig`. | `/proc/sys/kernel/sched_*`, schedtune cgroup files, scheduler tracepoints, per-CPU/core_ctl sysfs if present. |
| CPUFreq | `CONFIG_CPU_FREQ=y`, `CONFIG_CPU_FREQ_GOV_SCHEDUTIL=y`, `CONFIG_CPU_FREQ_DEFAULT_GOV_SCHEDUTIL=y`, `CONFIG_CPU_FREQ_STAT=y`, `CONFIG_CPU_FREQ_TIMES=y`; driver code selected through `CONFIG_CLOCK_CPU_OSM=y`. | `/sys/devices/system/cpu/cpufreq/policy*/` and per-CPU cpufreq nodes, `time_in_state`, transition stats, governor tunables. |
| CPU topology | `arch/arm64/boot/dts/qcom/sm8150.dtsi`, `cpus` and `cpu-map`; `capacity-dmips-mhz` values are 1024 for CPU0–3 and 1740 for CPU4–7; energy-cost phandles differ by cluster. | `/sys/devices/system/cpu/{online,possible,present}`, scheduler topology debugfs if enabled, and runtime policy masks. |
| Clock/frequency | `CONFIG_CLOCK_CPU_OSM=y`; `clock_cpucc` is compatible with `qcom,clk-cpu-osm` in `sm8150.dtsi`. Driver: `drivers/clk/qcom/clk-cpu-osm.c`. | CPUFreq policies and OSM driver name/table; actual OSM state depends on SoC firmware/hardware programming. |
| Idle/power | `CONFIG_CPU_IDLE=y`, menu governor, `CONFIG_MSM_PM=y`; Qualcomm LPM code built from `drivers/cpuidle/lpm-levels*.c`. | `/sys/devices/system/cpu/cpu*/cpuidle/state*`, `/sys/kernel/debug/msm_lpm`, suspend diagnostics, dmesg. Actual interface names vary. |
| Thermal/core control | CPU nodes include `#cooling-cells` and `qcom,lmh-dcvs`; scheduler core_ctl is a separate subsystem. | thermal zone/cooling state, CPU policy limits, `/sys/devices/system/cpu/cpu*/core_ctl/*`, online CPU mask. |

The DTS expresses a heterogeneous capacity/energy topology. It does **not** provide a conventional CPU OPP table or `cpu-idle-states` list in the inspected common SM8150/vayu files. The OSM table is read from controller registers; idle state definition/registration uses Qualcomm low-power node parsing and platform integrations. Whether the bootloader overlays or vendor userspace add other policy is a device validation question.

### Source changes attributable to Xen-Kernel

**VERIFIED:** Current M0/M1 changes touch only `.github/workflows/build-kernel.yml` and `scripts/xen-baseline/collect-device.sh` plus reports outside the kernel git repository. No CPU scheduler, cpufreq, clock, idle, thermal, or device-tree source was modified. The earlier initial audit also described source inspection only. The CI workflow's conditional `cpu.h` include concerns `drivers/soc/qcom/hyp_core_ctl.c`; it is a compile include workaround, not a CPU policy change. Workflow release metadata edits are build metadata, not runtime tuning.

## 3. WALT implementation analysis

**VERIFIED — source and configuration.** `CONFIG_SCHED_WALT` is defined in `init/Kconfig` (SMP dependency) and adds `kernel/sched/walt.o` and `boost.o` from `kernel/sched/Makefile`. Main implementation is `kernel/sched/walt.c`, interfaces and inline accounting in `kernel/sched/walt.h` and `kernel/sched/sched.h`, and fair class integration in `kernel/sched/fair.c`. The defconfig enables it.

WALT maintains runnable/task demand over scheduler windows, rather than relying only on PELT's exponentially decaying average. In this config the default window is 20 ms (`MIN_SCHED_RAVG_WINDOW` in `walt.c`; HZ=300 uses the rounded 19,999,998 ns expression). The early boot parameter `sched_ravg_window=` is bounded from that minimum through 1 s. Window history defaults to five samples and `WINDOW_STATS_MAX_RECENT_AVG`; actual values can be changed by runtime sysctls or boot arguments. `walt_update_task_ravg`, enqueue/dequeue hooks, `update_task_ravg`, and `walt_irq_work` maintain task/runqueue demand and report to consumers. Big-task and colocation metadata also feed task placement/core_ctl decisions.

Initialization: runqueue WALT initialization is called from scheduler initialization in `kernel/sched/core.c`; one-time setup initializes irq work and scale divisors. `register_walt_callback` registers CPUFreq policy/transition notifiers at `core_initcall`. WALT's scheduler operations are installed at `late_initcall(sched_init_ops)`. This couples its task accounting to both scheduler core startup and CPUFreq policy lifecycle.

Runtime sysctls actually registered in `kernel/sysctl.c` include `sched_cpu_high_irqload`, `sched_group_upmigrate`, `sched_group_downmigrate`, `sched_boost`, `sched_conservative_pl`, `sched_many_wakeup_threshold`, `sched_walt_rotate_big_tasks`, `sched_min_task_util_for_boost`, `sched_min_task_util_for_colocation`, `sched_little_cluster_coloc_fmin_khz`, `sched_upmigrate`, `sched_downmigrate`, and `sched_energy_aware`; `CONFIG_SCHED_DEBUG` adds controls including `sched_sync_hint_enable` and `sched_cstate_aware`. WALT history/window values are source defaults/boot parameters unless an additional runtime interface is shown; do not assume `sched_ravg_hist_size` or `sched_window_stats_policy` are sysctls. Scheduler tracepoints include `sched_load_to_gov`, scheduler utilization and wake events; exact names should be read from tracefs `available_events`. Debugfs scheduler state may include `sched_features`, `sched_debug`, and `schedstat`; do not infer runtime values from C initializers.

**STRONG HYPOTHESIS:** Window/history choice can trade responsiveness to short bursts against smoothing/noise and frequency overshoot. That is a candidate for controlled measurement only. It is not a demonstrated weakness; selecting another window based on a different kernel's default would not be evidence.

## 4. Scheduler placement and load balancing

**VERIFIED — source.** The fair scheduler in `kernel/sched/fair.c` owns `select_task_rq_fair`, `wake_affine`, `find_energy_efficient_cpu`, `find_best_target`, `load_balance`, and `rebalance_domains`. The wakeup path starts in `try_to_wake_up` and invokes class `select_task_rq`; `wake_up_new_task` handles fork placement in `kernel/sched/core.c`. Topology/capacity/energy information comes from ARM64 topology and DT `capacity-dmips-mhz` plus sched-energy-cost data.

The EAS-enabled path considers sync wake hints, task capacity fit, idle/prefer-idle state, task boost and group placement. Under `CONFIG_SCHED_WALT`, waking task demand can be included in placement. WALT/boost state changes capacity margins and candidate filtering; fit decisions are not a single “big core first” policy. The same code also retains wake-affine and conventional load-balancing paths. Periodic/new-idle balancing migrates eligible CFS tasks according to domain/group imbalance and capacity; task affinity, isolated/offline CPUs, RT/DL activity, and migration cost constrain choices.

Relevant controls include scheduler features under debugfs (`FIND_BEST_TARGET`, `EAS_PREFER_IDLE`, `WA_IDLE`, `WA_WEIGHT`, and other build-dependent features), `sched_sync_hint_enable`, `sched_cstate_aware`, capacity margins, up/down migration thresholds, `sched_migration_cost`, and `sched_nr_migrate`. These require inventory from the running build; some are not writable or present on production ROMs.

**DEVICE VALIDATION REQUIRED:** Source DTS topology establishes intended asymmetry, but the active scheduler topology, online mask, energy model registration, runtime EAS feature settings, app cpusets, and vendor task placement policy are not known. For gaming, include per-frame-thread CPU, wake-to-run delay, migration, runqueue delay, GPU busy/time and thermal state. Frame time alone cannot identify CPU placement as cause.

## 5. SchedTune analysis

**VERIFIED — source/config.** `CONFIG_SCHED_TUNE=y` is defined in `init/Kconfig`; controller code is `kernel/sched/tune.c`, math/task utility in `kernel/sched/fair.c`, interface structures in `kernel/sched/tune.h`, and boost transitions in `kernel/sched/boost.c`. `schedtune_init` uses `postcore_initcall`; root group boost initializes to zero. At most 16 groups are supported, with a two-level hierarchy (root and children). `boost` writes accept -100..100; group preferences include boost enable/override and prefer-idle. The schedtune controller must be mounted/exposed and vendor userspace must place tasks in groups for group policy to matter.

Boost uses signal-proportional compensation: positive boost adds margin proportional to remaining capacity; negative boost reduces by a proportion of current signal. It affects task utilization, CPU placement/fit, and frequency requests. Per-CPU active group boost is maintained from runnable enqueue/dequeue activity and a hold interval. `prefer_idle` influences placement. SchedTune also has “colocated” task/group machinery used by WALT.

Interfaces are cgroup-v1 `schedtune` files: `boost`, `prefer_idle`, and, with WALT, `sched_boost_no_override` and `colocate`. The separate `/proc/sys/kernel/sched_boost` is a global scheduler boost control. Exact mounted hierarchy and values are userspace/runtime facts. The collector preserves exposed scheduler sysctls; a separate cgroup inventory is needed to capture all live groups and their tasks without writing.

**STRONG HYPOTHESIS:** A persistent or broad positive boost can improve short wake/run or frame response but keep higher utilization/frequency demand longer, increasing energy and heat. Existing code has no evidence that vayu's active groups are excessive. First correlate boost values/group membership with workload and residency.

## 6. Schedutil and cpufreq analysis

### schedutil

**VERIFIED:** `CONFIG_CPU_FREQ_DEFAULT_GOV_SCHEDUTIL=y` and `CONFIG_CPU_FREQ_GOV_SCHEDUTIL=y`. Implementation is `kernel/sched/cpufreq_schedutil.c`; registration at `fs_initcall`. `sugov_init/start/stop/limits`, `sugov_update_single/shared`, `get_next_freq`, `sugov_update_commit`, and asynchronous worker paths coordinate policy setup and frequency updates. It registers scheduler update-util hooks. When WALT utilization is active, `sugov_get_util` calls `boosted_cpu_util` with WALT load; `sugov_walt_adjust` accounts for WALT new/previous load and high-load conditions. I/O wait boost is also applied. Rate limiting and policy sharing affect how promptly requests reach the driver.

The governor exposes policy tunables through policy sysfs (notably `rate_limit_us`; exact attrs depend on this vendor implementation and build). Measure actual update cadence, requested/current frequency, transition trace events, policy limits, and frequency residency. A governor name alone does not tell whether fast switching is available or whether thermal/DCVS constraints cap it.

### Qualcomm OSM CPUFreq

**VERIFIED:** `CONFIG_CLOCK_CPU_OSM=y` in the defconfig and `drivers/clk/qcom/Kconfig` defines it. The DTS controller at `clock_cpucc` in `arch/arm64/boot/dts/qcom/sm8150.dtsi` is `qcom,clk-cpu-osm`. `drivers/clk/qcom/clk-cpu-osm.c` registers at `subsys_initcall`, binds the OF match, initializes OSM registers/clock providers and registers `qcom_osm_cpufreq_driver`. That driver is named `osm-cpufreq`, sets `fast_switch`, and maps CPU policy domains through clock-parent/shared-domain relationships. The table is read from OSM hardware registers, converts values to kHz, filters entries marked single-core and entries below 300 MHz, and exposes available/boost frequencies. `osm_cpufreq_target_index` writes desired performance-state index; fast-switch takes a target and resolves table index.

This differs from `drivers/cpufreq/qcom-cpufreq.c` (`CONFIG_CPU_FREQ_MSM`, disabled in defconfig) and `cpufreq-dt` (also disabled). Research should treat OSM as the intended SM8150 driver based on compatible/config, but only runtime `scaling_driver`, policy masks, and successful probe confirm it on the specific boot image.

### Interactions and transition latency

The chain is scheduler enqueue/wakeup and WALT accounting → placement/capacity and boosted util → schedutil update-util callback and rate limiting → CPUFreq policy min/max/thermal constraints → OSM fast-switch index or frequency driver update → hardware OSM clock/voltage state. `cpufreq` transition events and `power:cpu_frequency` tracepoints can establish request/transition timing. Fast-switch capability reduces software handoff overhead, but does not establish total hardware response latency or energy optimality. Capture `cpuinfo_transition_latency`, `scaling_transition_latency` if present, trace request-to-transition and wake-to-running distributions.

## 7. Qualcomm core control analysis

**VERIFIED — scheduler `core_ctl`.** `CONFIG_SCHED_CORE_CTL=y` compiles `kernel/sched/core_ctl.c`. WALT calls `core_ctl_check` once per WALT window at its rotation/checkpoint path. Core_ctl reads per-CPU scheduler utilization (`sched_get_cpu_util`), updates running averages, evaluates cluster demand and thresholds, and wakes per-cluster `core_ctl/<first_cpu>` kthreads to isolate/unisolate CPUs. `core_ctl_init` is `late_initcall`; it registers CPU hotplug callbacks and creates per-CPU-device `core_ctl` sysfs groups. The sysfs inventory includes `min_cpus`, `max_cpus`, `offline_delay_ms`, `busy_up_thres`, `busy_down_thres`, `task_thres`, `nr_prev_assist_thresh`, `need_cpus`, `active_cpus`, `global_state`, `not_preferred`, and `enable` (read/write access varies).

The control is distinct from CPUFreq: it changes available/isolated cores on a slower policy cycle; schedutil controls requested frequency. WALT utilization therefore feeds both frequency and core-count demand. Additional paths include boost API from `kernel/sched/boost.c`, notifier callbacks, hotplug/isolation callbacks, and core_ctl trace events. Thresholds and whether it actively offlines cores need runtime capture.

**VERIFIED — Qualcomm hypervisor reservation driver.** `CONFIG_QCOM_HYP_CORE_CTL=y` depends on `OKL4_GUEST`, also enabled. `drivers/soc/qcom/hyp_core_ctl.c` parses `qcom,hyp-core-ctl` DT `reg` data, starts a high-priority kthread, exposes `enable/status` under the CPU sysfs root, debugfs `hyp_core_ctl/reserve_cpus`, integrates with hotplug and CPU cooling max-level notifications, and talks to OKL4 hypervisor affinity syscalls. This is CPU reservation for a guest, not the scheduler demand-based `core_ctl`. No matching compatible string was found in the checked-in vayu/SM8150 DTS. **DEVICE VALIDATION REQUIRED:** do not assume it probes or reserves cores on vayu because its config is enabled.

Potential interaction with thermal: scheduler core_ctl can alter active/isolated count; the hypervisor driver explicitly tracks thermal CPU masks and swaps/reserves CPUs around cooling constraints. Thermal/cooling state and online/isolated masks must be recorded together. Do not change core_ctl or cooling values during baseline work.

## 8. CPU idle and wakeup latency

**VERIFIED:** `CONFIG_CPU_IDLE=y`, menu governor, `CONFIG_CPU_IDLE_MULTIPLE_DRIVERS=y`, `CONFIG_MSM_PM=y`; the latter selects multiple Qualcomm low-power drivers in `drivers/soc/qcom/Kconfig`. `drivers/cpuidle/lpm-levels.c`, `lpm-levels-of.c`, `lpm-levels.h`, `lpm-workarounds.c`, `drivers/soc/qcom/msm-pm.c`, `spm.c`, and ARM64 PSCI integration implement CPU/cluster idle and suspend. The OF LPM parser consumes Qualcomm low-power level nodes and state properties such as minimum residency and exit latency; selection estimates next wakeup and compares residency/latency boundaries. MSM PM includes WFI, retention, fast power collapse and power-collapse entry paths (availability depends on platform state definitions and firmware).

Runtime interfaces include per-CPU `cpuidle/state*/{name,desc,latency,residency,time,usage,disable}`; cpuidle governor; Qualcomm debugfs LPM state/limits/statistics; power tracepoints; wakeup sources; and `/sys/power/suspend_stats` on kernels that expose them. `CONFIG_CPU_IDLE` alone does not prove a particular state is registered or used. Common SM8150/vayu DTS inspected here does not show standard `cpu-idle-states`; vendor runtime state must be checked.

Wakeup latency is the sum of IRQ routing, idle exit, scheduler wakeup/placement, frequency response, and userspace dispatch. A single `cpuidle` exit-latency value is not app wake-to-frame latency. Use trace events (IRQ, `sched_waking`, `sched_wakeup`, `sched_switch`, CPU idle, CPU frequency) and a monotonic userspace marker; repeat at controlled idle residency and thermal/charge conditions. Measure p50/p95/p99 and tail latency, not only mean.

## 9. Thermal interaction

CPU nodes in `sm8150.dtsi` include `#cooling-cells` and `qcom,lmh-dcvs` phandles. The SoC has Qualcomm LMH hardware paths and thermal/cooling framework; cpufreq and scheduler utilization may request capacity above what a thermal limit permits. CPU cooling can impose policy ceilings or mark cores thermal-managed. The hypervisor core reservation code receives maximum-level notifications. Vayu overlay `vayu-sm8150.dtsi` contains charger/battery thermal zones; general SoC thermal zones are in SM8150 DTS files.

**VERIFIED:** thermal can constrain CPU frequency and core availability through cooling integration; user-visible peak frequency may therefore be transient. **DEVICE VALIDATION REQUIRED:** source declarations do not establish which zones, LMH notifications, cooling bindings, firmware controllers, skin policies, or limits are active in a particular ROM. Record CPU thermal zones, cooling-device type/state, policy max/min, online and isolated masks, battery temperature, and workload residency concurrently. Do not tune thermal trips/safety limits.

## 10. Runtime tunables inventory

Read-only inventory to capture before any candidate:

| Interface | Values to preserve | Notes |
|---|---|---|
| `/proc/sys/kernel/sched_*` | Registered WALT group migration/boost thresholds, `sched_boost`, capacity up/down migration margins, EAS, sync/cstate hints and other debug controls. | Read actual names; some WALT window/history values are defaults or boot parameters, not registered sysctls. |
| `/sys/fs/cgroup/schedtune/` or mounted legacy hierarchy | Root/child `boost`, `prefer_idle`, `sched_boost_no_override`, `colocate`, membership. | Read controller mount and all groups. Keep task names/IDs consistent across runs. |
| `/sys/devices/system/cpu/cpu*/core_ctl/` | thresholds, delay, `need_cpus`, active count, state, enable, preferred CPUs. | Distinguish read-only state from writable tunables; collector reads only. |
| `/sys/devices/system/cpu/cpufreq/policy*/` | `scaling_driver`, governor, related/affected CPUs, available frequencies, min/max/current, transition latency, stats/time-in-state, governor tunables. | Confirm `osm-cpufreq`; policy masks should be measured rather than inferred from clusters. |
| `/sys/devices/system/cpu/cpu*/cpuidle/` | governor, state names/latency/target residency/disable/usage/time. | Capture deltas around each workload. |
| `/sys/devices/system/cpu/{online,isolated}` and debugfs scheduler topology | online, isolated, possible, present, cluster/capacity group mapping. | Distinguish offline from scheduler-isolated. |
| Tracefs | available events; enable only a small documented set during dedicated runs; timestamp clock and buffer settings. | Tracing has overhead; use matched instrumented baseline/candidate or a separate low-overhead run. |
| Thermal/cooling | every CPU-related zone and cooling device current/max state. | No writes. |

The revised collector captures `/proc/sys/kernel/sched_*`, per-CPU cpufreq/core_ctl/cpuidle files, and targeted Qualcomm interfaces where present; its manifest identifies missing/inaccessible files. Cgroup-wide schedtune membership and high-resolution trace data still require a separate collection procedure.

## 11. Measurement methodology

Follow [RUNTIME_BASELINE.md](RUNTIME_BASELINE.md) for controlled charge/ambient/screen/network/workload/cooldown conditions and repetition/reporting. Minimum CPU experiment datasets:

1. Per-policy and per-CPU frequency residency, current/requested frequency where observable, CPU idle state residency, CPU online/isolated state, and thermal/cooling state.
2. `sched_waking`→`sched_wakeup`→`sched_switch` latency for representative UI/frame-thread wakeups; include IRQ and CPU-idle traces for a targeted run.
3. Per-thread CPU, migration count, runqueue delay, WALT utilization/demand, schedtune group/boost and `core_ctl` counts during interactive and gaming scenes.
4. Frame-time distribution, 1% low calculated from a stated convention, GPU busy/idle and frequency, sustained device temperatures, and battery current/energy for the same scene.
5. Sustained CPU throughput alongside temperature, frequency residency, core counts, and energy. Include a short burst and longer thermal steady-state block.
6. Screen-off idle/suspend drain, wake-to-usable time, suspend failures and wake sources.

Use at least five randomized repeat runs and report medians plus spread/tails. Keep stock vendor userspace, app, display, network, charge band, and ambient conditions fixed. Treat tracing overhead as a separate controlled factor. Do not interpret the final `scaling_cur_freq` sample as residency or infer power from requested frequency alone.

## 12. Evidence-supported bottlenecks

**VERIFIED:** The CPU stack is complex and coupled: WALT demand informs fair placement and schedutil; schedtune and task boosts influence both fit/placement and utilization; WALT periodically drives core_ctl; CPUFreq OSM exposes fast-switch; thermal cooling can cap frequencies and core availability. SM8150 has heterogeneous capacity/energy information.

**No runtime bottleneck is evidenced.** There is no captured delayed wakeup, excessive low-frequency residency, inappropriate big-core placement, avoidable migration, idle-state miss, thermal cap, core_ctl lag, excessive scheduler wakeup cost, or battery regression in available evidence. These remain questions, not findings.

## 13. Optimization candidates ranked by priority

Rank indicates research order by evidence value and reversibility, not expected speedup. All are hypotheses, and **none is approved for implementation**.

| Rank / candidate | Current path and limitation hypothesis | Potential benefit and energy/thermal trade-off | Evidence required, patch scope, difficulty and risk | Rollback |
|---|---|---|---|---|
| 1. Improve observation and correlate scheduler→frequency→thermal events | Existing code exposes WALT/schedutil/core_ctl tracepoints and counters, but there is no target dataset. Missing visibility can make policy tuning target the wrong layer. | No direct performance claim; highest chance of identifying a true bottleneck with no runtime policy change. Trace overhead may perturb short latency. | Physical device, synchronized low-overhead tracing plus workload logs. Patch scope: none initially; later add only targeted trace/collector support if required. Difficulty low-medium; risk low. | Remove trace config/use or revert tooling-only changes. |
| 2. Evaluate WALT window/history against task wake and frame demand | WALT window defaults to 20 ms, five history samples, max-recent average. Could lag or overshoot a particular burst pattern; no evidence it does so. | Potentially improve wake/frequency responsiveness or reduce overshoot. Shorter window can increase noise/frequency churn, CPU work, energy and heat; longer smoothing may hurt input/frame response. | Matched WALT traces, schedutil requests/residency, wake latency, frame time and energy. Candidate scope: WALT boot/sysctl policy or narrowly scoped accounting only after diagnosis. Difficulty medium-high; risk medium-high due cross-subsystem effects. | Restore original bootarg/tunable or revert isolated patch. |
| 3. Measure schedutil WALT adjustment/rate-limit behavior | Governor consumes boosted WALT utilization, I/O-wait boost and policy rate-limit. A rate-limit or high-load adjustment could under/overshoot. | Could reduce ramp delay or unnecessary high states; more aggressive response can raise power/thermal load and lower sustained headroom. | Compare requested/current frequency and `schedutil` update traces against wake/exec timing and temperature. Scope one tunable or one algorithmic condition at a time. Difficulty medium; risk medium. | Restore prior tunable or revert patch. |
| 4. Evaluate placement policy/features for measured migration or capacity misses | EAS/FIND_BEST_TARGET, prefer-idle, sync wake, WALT fit and SchedTune boosts can produce complex choices. Potential limitation only if traces show poor target, wake-affine mistake, or repeated migration. | Better task locality/frame pacing possible; overpacking little cores or pushing work to big cores can increase contention/energy/heat. | Per-frame-thread wake/placement/migration, capacity, runqueue delay, GPU wait and thermal correlation. Scope fair placement one feature/condition at a time. Difficulty high; risk high due broad impact. | Revert isolated scheduler patch; maintain bootable baseline image. |
| 5. Evaluate scheduler core_ctl response / offline delay | WALT-window checking plus need thresholds and `offline_delay_ms` may affect core availability during transient/sustained bursts. No active values or traces are known. | Could avoid late capacity availability or excess active cores. Faster online may increase idle/transition energy and thermal load; fewer cores may worsen parallel throughput. | Read actual cluster sysfs, online/isolation timeline, WALT demand, hotplug latency, workload frame/throughput and energy. Scope core_ctl hysteresis only if isolated evidence. Difficulty high; risk high, potential hotplug/suspend regression. | Restore original tunables or revert source; test boot/suspend after change. |
| 6. Evaluate CPU idle state prediction only if measured wake tails or idle churn | Qualcomm menu/LPM selection uses next-event, residency history, exit latency and platform states. A prediction miss may add wake latency; not shown in current evidence. | Better state selection can reduce idle energy or tail latency. Shallower idle can cost battery; deeper idle can worsen wake latency. | Idle trace plus wake-to-run latency, state usage/residency, event timing, idle power/charge drain and suspend correctness. Scope LPM prediction or state constraints only with device owner review. Difficulty high; risk high. | Restore default policy/state config; preserve recovery and boot path. |

Across all candidates, a synthetic benchmark increase is insufficient. Require interactive, gaming frame pacing, sustained performance, energy, and temperature results, plus boot/suspend/recovery checks.

## 14. Risks and regressions

- WALT and schedutil share utilization inputs with placement/core control; changing accounting may alter multiple policy consumers at once.
- SchedTune can amplify demand and affect both frequency and CPU placement. Runtime userspace may overwrite values after boot.
- Core hotplug/isolation changes can affect task affinity, workqueues, IRQ placement, suspend, and scheduling latency.
- EAS policy changes can improve one workload while harming background efficiency or thermal headroom.
- CPU idle changes can affect suspend reliability, wake sources, latency tails, and energy.
- OSM frequencies derive from hardware/controller state, and thermal/firmware caps can differ from static source expectations.
- Trace instrumentation affects timing and must be matched across conditions.

No candidate authorizes changes to CPU frequency ceilings, overclocking, thermal trips, GPU clocks, or charging settings.

## 15. Recommended CPU experiment roadmap

1. Collect read-only policy/topology/sysctl/cgroup/thermal/cpuidle snapshots on the actual baseline vayu and confirm runtime driver, active WALT/SchedTune groups, core_ctl settings, OSM masks/table, and LPM states.
2. Establish idle, interactive, gaming/frame pacing, sustained CPU, and suspend/resume baselines under `RUNTIME_BASELINE.md` conditions.
3. If a measurable issue appears, capture a targeted trace to classify it: task wake/placement, frequency request/transition, core availability, idle exit, or thermal cap.
4. Form one falsifiable change hypothesis and choose one control plane; preserve default source/config and test one patch at a time with an explicit rollback image.
5. Compare medians and tails for response/frame pacing, sustained throughput, energy/current, and temperature. Reject changes that trade a synthetic score for worse thermals, energy, or frame-time spread.
6. Review all results with the technical lead before M3 or implementation.

## 16. References and source paths

- `init/Kconfig`: `SCHED_WALT`, `SCHED_CORE_CTL`, `SCHED_TUNE`.
- `arch/arm64/configs/vayu_defconfig`: WALT/SchedTune/core_ctl, schedutil, CPU idle, MSM PM, OSM, hypervisor guest config.
- `kernel/sched/walt.c`, `walt.h`, `sched.h`: window accounting, init, frequency reporting, core_ctl callback.
- `kernel/sched/fair.c`: WALT task utilization, wakeup/energy placement, load balancing, SchedTune margins.
- `kernel/sched/core.c`: wake path, task initialization, scheduler startup.
- `kernel/sched/tune.c`, `tune.h`, `boost.c`: SchedTune groups, boosts, cgroup interfaces and core_ctl boost integration.
- `kernel/sched/core_ctl.c`, `core_ctl.h`: utilization-driven core count, hotplug/isolation, sysfs and trace events.
- `kernel/sched/cpufreq_schedutil.c`: update-util hooks, WALT utilization and frequency selection.
- `drivers/clk/qcom/Kconfig`, `drivers/clk/qcom/clk-cpu-osm.c`: SM8150 OSM clock/CPUFreq driver.
- `drivers/cpufreq/Kconfig`, `drivers/cpufreq/qcom-cpufreq.c`: generic Qualcomm MSM driver (disabled in defconfig; not to be conflated with OSM).
- `drivers/cpuidle/lpm-levels.c`, `lpm-levels-of.c`, `drivers/soc/qcom/msm-pm.c`, `spm.c`: Qualcomm idle/power paths.
- `drivers/soc/qcom/hyp_core_ctl.c`, `drivers/soc/qcom/Kconfig`: optional OKL4 CPU reservation driver.
- `arch/arm64/boot/dts/qcom/sm8150.dtsi`, `sm8150-v2.dtsi`, `vayu-sm8150-overlay.dts`, `xiaomi/overlay/vayu/vayu-sm8150.dtsi`: CPU topology, capacity/energy, OSM, cooling and device overlay.
- `kernel/sysctl.c`, `Documentation/cpu-freq/`, `Documentation/power/`: runtime control registrations and generic Linux 4.14 interface background. Generic docs do not prove vendor runtime state.

## 17. Unknowns requiring physical-device testing

1. Which exact kernel and merged DT/overlays boot on the phone; actual OSM driver probe, cpufreq policies, frequency table, policy masks, min/max, and fast-switch behavior.
2. Active WALT sysctls/boot parameters, WALT trace values, schedtune cgroups and userspace managers, EAS feature flags, cpusets and app thread placement.
3. Core_ctl cluster sysfs values, active/isolated CPU sets, observed decision/online delays, and whether `hyp_core_ctl` actually probes.
4. Registered cpuidle states/governor, MSM LPM configuration, idle residency, exit latency, wake-source behavior, and suspend success.
5. Actual thermal/LMH controls, CPU cooling caps, firmware effects, battery/skin temperature, and interactions during sustained gaming/CPU load.
6. Wake-to-run and frequency-transition latency distributions, task migration/runqueue delay, FPS/frame-time spread, sustained performance, and energy/battery usage.
7. ROM/app-specific scheduler and cpufreq writes after boot; available tracepoints/debugfs/sysfs permissions.

Until those are measured, all optimization candidates remain hypotheses. No CPU tuning is implemented in this task.


## Additional CPU source review checkpoint

The remaining WALT window/history, placement, SchedTune, core_ctl, OSM, and cpuidle candidate classes remain coupled to runtime policy, firmware, topology, and workload. Existing reports map their source paths and interfaces, but this checkout has no trace proving one of them is the limiting path. No arbitrary CPU-003 scheduler constant or core_ctl policy was introduced. CPU-001/CPU-002 remain the only source behavior experiments until same-SHA builds and traces distinguish frequency ramp limiting from placement, idle exit, or thermal cap. This is an engineering hold on speculative tuning, not a claim those subsystems are optimal.
