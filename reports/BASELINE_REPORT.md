# Xen-Kernel baseline report

## Identity and evidence

- Target: Poco X3 Pro, codename vayu, Qualcomm SM8150, ARM64.
- Kernel source: Linux 4.14.357 vendor tree.
- Baseline branch: `16` at `bf6ac1247feda28293062995d445506b050aec8a`.
- Experiment branch: `experiment/m0-m1-reproducible-baseline` at `1d7baee8d8363b1a1369bd1b3e654e30d5d5cc87`, tracking `origin` at inspection. `git diff origin/16...HEAD` contains CI/provenance patches and the collector only; kernel subsystem source/config is unchanged.
- Worktree was clean before this mission's documentation and collector additions.

**Runtime measurements: none.** No Actions run is listed for the experiment branch; no rooted Poco X3 Pro, ADB, fastboot, benchmark data, trace, image or runtime log is attached. All statements below are static configuration/source observations, not device state.

## Static baseline characteristics

| Subsystem | Checked-in evidence | Not established |
|---|---|---|
| CPU topology | `sm8150.dtsi` describes eight CPUs, four capacity entries 1024 and four entries 1740, CPU maps, energy cost data, and LMH links. | Runtime-online/isolated masks, firmware state, actual capacity, policy topology. |
| Scheduling | `vayu_defconfig` enables WALT, SchedTune, scheduler core_ctl, and scheduler utilization-related code. Existing WALT logic couples demand accounting, placement and core control. | Active WALT sysctls/boot args, Android task groups, actual placement, wake latency, runqueue delays. |
| CPU frequency | Defconfig has CPUFreq, schedutil default/governor, stats; SM8150 DTS advertises CPU OSM. | Runtime driver, policy masks/tables/current limits, residency, fast-switch behavior, transition times. |
| CPU idle | CPU idle/menu and Qualcomm MSM PM are configured. | Registered low-power states, residency, exit latency, suspend reliability. |
| GPU | KGSL and KGSL IOMMU are configured; Qualcomm Adreno devfreq governor support is present. | Actual Adreno revision/driver probe, governor, levels, utilization, frame pacing, thermal caps. |
| Memory/ZRAM | Swap, memcg, ZRAM, zsmalloc are enabled; LZ4 is the source default; ZRAM optional dedup/writeback are disabled. CMA config is 16 MiB and 7 areas. | Runtime compressor/size/swap priority, pressure, reclaim, compression ratio, CMA allocation failures. |
| Storage/I/O | Defconfig includes noop, deadline, CFQ and multi-queue deadline/Kyber implementations. | Actual UFS/eMMC node, queue mode, scheduler, queue depth, latency, filesystem behavior. |
| Thermal/power | Thermal framework, CPU/devfreq thermal, TSENS, step-wise and user-space governors, QCOM LMH/thermal drivers are configured. Vayu overlay contains charger/battery thermal zones. | Merged DT, live trip tables, userspace thermal manager, cooling state, temperatures, power budgets. |
| Battery/charging | Power-supply and LN8000 charger driver symbols are set; vayu overlay carries charger/battery data. | Battery health/capacity, current/voltage draw, ROM charging policy, energy per workload. |

## Baseline protocol and results

Use `RUNTIME_BASELINE.md`, `DEVICE_BASELINE_GUIDE.md`, and `CPU_BASELINE_CHECKLIST.md`. Required scenarios include idle/suspend, interactive response, a repeatable GPU game scene, CPU sustained load, memory pressure, storage I/O, and mixed CPU/GPU gaming. Collect at least five repetitions per condition and report every run, median and spread. Preserve raw output and conditions.

Measured results table: **empty**. No source-only fact is presented as a performance result.
