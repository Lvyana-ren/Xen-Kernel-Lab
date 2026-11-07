# Xen-Kernel initial audit

**Scope:** read-only source inspection of branch `16` at `bf6ac1247fed` (`Update build-kernel.yml`). The worktree was clean at inspection. The top-level Makefile identifies this as Linux **4.14.357**, with source `EXTRAVERSION = -openela`; the workflow edits that version string during its build. No files were changed, and I did not build the kernel.

**Evidence labels:** **Verified** means directly visible in the checked-in source or configuration. **Hypothesis / research item** means a possible effect that needs runtime data, device testing, or deeper source tracing to establish.

## 1. Repository architecture

This is a broad Linux kernel tree with Qualcomm and Xiaomi vayu support:

- `arch/arm64/` contains ARM64 platform code, the vayu defconfig, and Qualcomm device trees.
- `drivers/` contains SoC, scheduler, GPU, memory, thermal, charging, and power drivers.
- `include/`, `kernel/`, `mm/`, and `init/` contain shared kernel interfaces, core scheduling, memory management, and boot initialization.
- `scripts/` and `tools/` support configuration, builds, and developer utilities.
- `.github/workflows/` contains the CI build automation.

Device-specific sources include:

- `arch/arm64/configs/vayu_defconfig`
- `arch/arm64/configs/vendor/xiaomi/vayu.config`
- `arch/arm64/boot/dts/qcom/vayu-sm8150-overlay.dts`
- `arch/arm64/boot/dts/qcom/xiaomi/overlay/vayu/vayu-sm8150.dtsi`

The vendor config contains `CONFIG_MACH_XIAOMI_VAYU=y`; the overlay includes vayu audio, pinctrl, and camera descriptions.

## 2. Hardware and subsystem map

| Area | Main source locations | Verified configuration or behavior |
|---|---|---|
| CPU and scheduling | `kernel/sched/`, `drivers/cpufreq/`, `drivers/soc/qcom/hyp_core_ctl.c`; `init/Kconfig` | `CONFIG_SCHED_WALT`, `CONFIG_SCHED_TUNE`, `CONFIG_SCHED_CORE_CTL`, `CONFIG_CPU_FREQ`, `CONFIG_CPU_IDLE`; default CPUFreq governor is `schedutil`. Relevant symbols are defined in `init/Kconfig` and `drivers/cpufreq/Kconfig`. |
| GPU | `drivers/gpu/msm/`, `drivers/devfreq/governor_msm_adreno_tz.c` | `CONFIG_QCOM_KGSL=y`, `CONFIG_QCOM_KGSL_IOMMU=y`, and default governor string `msm-adreno-tz`. `drivers/gpu/msm/Kconfig` describes KGSL as the Adreno driver and selects its devfreq governors. |
| Memory | `mm/`, `drivers/block/zram/`, `drivers/devfreq/`, Qualcomm LLCC and bandwidth-monitor drivers | `CONFIG_SWAP`, `CONFIG_MEMCG`, `CONFIG_MEMCG_SWAP`, `CONFIG_ZRAM`, `CONFIG_ZSMALLOC`; ZRAM deduplication and writeback are disabled. The checked-in `zram_drv.c` default compressor is `lz4`. |
| Thermal | `drivers/thermal/`, `drivers/devfreq/devfreq_cooling.c`, vayu device tree | `CONFIG_THERMAL`, `CONFIG_CPU_THERMAL`, `CONFIG_DEVFREQ_THERMAL`, `CONFIG_THERMAL_TSENS`; default thermal governor is step-wise, with user-space governor also enabled. |
| Charging and battery | `drivers/power/supply/`, `drivers/power/`, vayu overlay and battery data | `CONFIG_POWER_SUPPLY`, `CONFIG_CHARGER_LN8000`; the overlay contains PM8150B charging limits, thermal mitigation tables, and NVT/Sunwoda 5160 mAh battery-data includes. |
| Power management | `drivers/cpuidle/`, `drivers/soc/qcom/`, `drivers/thermal/`, device tree | `CONFIG_CPU_IDLE`, Qualcomm `CONFIG_MSM_PM`, and `CONFIG_QCOM_HYP_CORE_CTL`; the vayu tree includes charger thermal zones and battery charging policy. |

The defconfig has `CONFIG_CMA_SIZE_MBYTES=16`, `CONFIG_CMA_AREAS=7`, and 4 KiB ARM64 pages. These are concrete configuration facts, but whether CMA sizing constrains this device’s multimedia workloads depends on runtime allocations and the final merged device tree.

## 3. Optimization configuration

### Checked-in baseline

`arch/arm64/configs/vayu_defconfig` enables performance-oriented and platform-specific features:

- `CONFIG_CC_OPTIMIZE_FOR_PERFORMANCE=y`
- `CONFIG_LTO=y`, `CONFIG_LTO_CLANG=y`, `CONFIG_LTO_CLANG_THIN=y`
- WALT, scheduler tuning, core control, and `schedutil`
- Adreno KGSL with the `msm-adreno-tz` governor
- ZRAM with LZ4 as the source default compressor
- Thermal governors, CPU thermal support, and devfreq thermal support

### Workflow-specific build configuration

`.github/workflows/build-kernel.yml` starts from `vayu_defconfig` and applies:

- ThinLTO via `CONFIG_LTO`, `CONFIG_LTO_CLANG`, and `CONFIG_THINLTO`
- `CONFIG_CC_OPTIMIZE_FOR_PERFORMANCE`
- `LOCALVERSION="-Xen+3"`
- Clang r547379, LLVM integrated assembler, and `ld.lld`

The workflow checks that LTO and performance optimization survive `olddefconfig`. It does not export all of the resulting configuration knobs as explicit artifacts in the repository; it copies the generated config to build artifacts when run.

**Configuration caveat:** the source defconfig names ThinLTO as `CONFIG_LTO_CLANG_THIN`; the workflow manipulates/checks `CONFIG_THINLTO`. This audit did not run Kconfig, so whether these names resolve to the same effective setting in this tree is **unverified**. The workflow’s own post-`olddefconfig` checks are the relevant evidence when a build is run.

## 4. GitHub Actions build workflow

`.github/workflows/build-kernel.yml` is manually dispatched (`workflow_dispatch`) and checks out branch `16`. It:

1. Installs Ubuntu build dependencies and restores ccache.
2. Downloads Clang r547379 if it is absent.
3. Checks expected files, toolchains, source commit, and kernel version.
4. Conditionally edits `drivers/soc/qcom/hyp_core_ctl.c` to add `#include <linux/cpu.h>`.
5. Conditionally edits `drivers/block/zram/zram_drv.c` to set the ZRAM default compressor to LZ4.
6. Configures the vayu defconfig, applies LTO and performance options, and checks the resulting config.
7. Strips `-openela` from the Makefile’s `EXTRAVERSION`.
8. Builds `Image` and uploads diagnostics and kernel artifacts, retaining them for seven days.

The workflow’s two source edits are conditional, but the checkout is still an independent build input to reproduce. The current source already has LZ4 as the ZRAM default, so that step reports no change for this revision. The workflow’s `hyp_core_ctl.c` edit depends on its include check and source contents.

**Potential workflow concern (verified):** the workflow changes `Makefile` and may change driver source in its checkout, but those changes are not committed or pushed. This is normal for CI, though resulting artifacts should be associated with the recorded source commit and the emitted workflow patch diff when comparing builds.

## 5. Optimization opportunities with restrained thermal and battery impact

These are research directions, not proposed immediate changes:

1. **Measure CPU scheduling and frequency behavior first.** WALT, `schedutil`, scheduler tuning, and core control are already enabled. Compare frequency residency, idle residency, wakeups, and task placement under fixed workloads before considering governor or scheduler changes. Tuning aggressiveness may improve short bursts but raise power and heat.
2. **Measure GPU governor behavior.** KGSL uses `msm-adreno-tz`; characterize frame-time stability, GPU frequency residency, and thermal throttling before changing governor policy. Higher performance ceilings may increase heat and battery draw, with little sustained benefit after throttling.
3. **Inspect ZRAM runtime settings.** LZ4 is the checked-in default, but actual device initialization and runtime settings determine the active compressor and size. LZ4 can reduce CPU cost at the expense of compression ratio; changing algorithms trades CPU time, memory pressure, and energy.
4. **Review enabled diagnostics and observability cost.** Scheduler debug/statistics options are enabled in the defconfig (`CONFIG_SCHED_DEBUG`, `CONFIG_SCHED_INFO`, `CONFIG_SCHEDSTATS`). Their real overhead depends on implementation paths and use; quantify before disabling, since they can help diagnose regressions.
5. **Preserve thermal and charging safeguards.** The device tree has thermal mitigation tables for charging and thermal-zone configuration. Changing charge limits or thermal trips may affect safety, battery longevity, and sustained performance; there is no low-risk performance rationale for such changes without measurement and hardware-specific validation.

A conservative optimization process should prioritize reducing unnecessary work and fixing demonstrated bottlenecks over raising CPU/GPU limits.

## 6. Boot risks and performance regression risks

### Verified risks to track

- **Toolchain/config coupling:** the build relies on an older Android Clang toolchain and ThinLTO. Toolchain changes or Kconfig symbol mismatches can affect build success or generated output. The workflow checks parts of this configuration but this audit did not execute it.
- **Workflow source mutation:** CI conditionally patches source before compiling. Comparing a local build against CI requires accounting for those edits.
- **Device-tree dependence:** vayu charging, battery, and thermal policy is defined in the device overlay. A wrong overlay selection or incompatible base tree can break device behavior independently of kernel config.
- **Thermal configuration is active:** changing frequency or thermal policy could trigger earlier throttling or alter charging behavior.

### Hypotheses requiring boot/device validation

- Changes to CPU idle, core control, scheduler placement, memory pressure, KGSL, or thermal mitigation can cause suspend, wakeup, frame-time, or battery regressions even when compilation succeeds.
- CMA or memory-policy changes may affect camera/display/multimedia allocations.
- Removing platform-specific driver support to reduce config size risks runtime failures if device-tree nodes or userspace depend on it.

No definite boot blocker was established from this read-only inspection.

## 7. Prioritized research roadmap

1. **Capture a reproducible baseline:** record the effective config and workflow artifacts for this commit; inspect the emitted source-patch diff and kernel release.
2. **Map runtime policy:** on-device collect CPU/GPU frequency and idle residency, thermal-zone and cooling-device state, charging state, ZRAM settings, and relevant kernel logs.
3. **Establish repeatable workloads:** idle drain, mixed interactive use, sustained CPU, sustained GPU, camera/multimedia, and charging under controlled ambient conditions.
4. **Correlate measurements:** identify whether latency, power, throttling, memory pressure, or charging behavior is the actual bottleneck before selecting a code area.
5. **Evaluate one subsystem at a time:** test CPU policy first, then GPU/devfreq, then memory/ZRAM; leave thermal and charging limits unchanged unless investigating a demonstrated safety or policy defect.
6. **Validate boot and recovery:** after any future change, validate boot, suspend/resume, thermal response, charging, camera/display, and recovery path on the target device.

**Sources inspected:** `.github/workflows/build-kernel.yml`; `Makefile`; `arch/arm64/configs/vayu_defconfig`; `arch/arm64/configs/vendor/xiaomi/vayu.config`; `arch/arm64/boot/dts/qcom/vayu-sm8150-overlay.dts`; `arch/arm64/boot/dts/qcom/xiaomi/overlay/vayu/vayu-sm8150.dtsi`; `drivers/gpu/msm/Kconfig`; `drivers/block/zram/zram_drv.c`; `drivers/cpufreq/Kconfig`; `drivers/thermal/Kconfig`; `drivers/soc/qcom/Kconfig`; `init/Kconfig`.
