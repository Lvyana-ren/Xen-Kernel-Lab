# Thermal and power source research

## Static configuration and source map

The vayu defconfig enables the thermal framework, writable trips, step-wise default governor, user-space governor, CPU thermal, devfreq thermal and TSENS. It also enables Qualcomm MSM PM, QCOM hypervisor core-control support, KGSL and power-supply/charger drivers. `sm8150-thermal.dtsi` contains LMH DCVS and SoC zones/cooling links; `drivers/thermal/qcom/msm_lmh_dcvs.c`, `tsens.c`, `drivers/thermal/thermal_core.c`, `thermal_sysfs.c`, `devfreq_cooling.c`, and KGSL `kgsl_pwrctrl.c` implement relevant controls. Vayu overlay contains charger and battery thermal data and numerous user-space-managed thermal zones.

These facts describe available policy and source topology. They do not identify the final merged DT, ROM thermal daemon, current trip values, LMH firmware state, CPU/GPU cooling caps, or temperature. Writable trip support is preserved; no trip or safety limit was altered.

## Power interactions

CPU OSM and schedutil, KGSL power levels and devfreq, CPU core control, LMH/thermal cooling, memory bandwidth votes and Android thermal services share a finite power/thermal budget. Raising CPU or GPU availability can improve a short burst but consume headroom for later frames and raise battery energy. Cooling changes can also alter CPU online policy and devfreq constraints. Measure CPU/GPU residency, online state, cooling states, battery and skin/SoC temperatures together during long mixed workloads.

Battery and charger sources include power-supply/PMIC drivers and the vayu overlay. Battery current sign/scale and charger state are vendor-dependent. Use raw reported values plus charge counter/energy over sufficiently long controlled runs; do not modify input current, charge voltage, charging policy or battery limits.

## Status and gate

No physical thermal or energy measurements exist. Do not tune thermal trips, cooling maps, CPU/GPU clocks, charger policy or power budgets. Any future experiment requires a measured limitation, sustained comparison, stability and suspend checks, and explicit confirmation that protection remains intact.

## Follow-up source review — 2026-11-07

SM8150 DTS contains CPU/GPU cooling links and Qualcomm LMH/TSENS zones; KGSL power-level application intersects thermal maximum/minimum bounds in `kgsl_pwrctrl.c`. This confirms CPU/GPU candidate experiments must be tested with thermal/cooling state and energy data. It does not establish that a particular zone or firmware policy is active in the phone's final merged DT/ROM. No thermal, power-budget, charging or trip modification is safe to select from this source-only state.


## M6 implementation decision

No thermal/power behavior experiment is safe to select without a device temperature/current timeline: TSENS, LMH, cooling, KGSL constraints, and ROM thermal services are jointly active unknowns, and changing trips/cooling maps would touch safety behavior. Existing collector snapshots provide point thermal/cooling/battery data; the next M6 measurement should sample them at a modest interval during a sustained mixed workload and correlate with CPU/GPU frequency/residency. No thermal, power-budget, charging, or frequency-limit code was changed. M6 remains measurement-gated.
