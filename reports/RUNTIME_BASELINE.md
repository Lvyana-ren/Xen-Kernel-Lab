# Runtime baseline protocol

This is a measurement protocol, not a record of measured results. **No physical-device collection or benchmark has been performed.** Use the same Poco X3 Pro, ROM/userspace, kernel source/config, battery, test apps, and measurement tools throughout each comparison. Capture raw data and the collector's `metadata.txt` and `manifest.tsv`; an unavailable node is missing evidence, never a zero reading.

## Controlled conditions

- **Battery:** start each run in the 50–80% state-of-charge band, unplugged for performance and drain tests. Record capacity, voltage, current, temperature, health, and whether charging is connected. For charging observations, start at a repeatable 30–50% band, use the same charger/cable/source, and never alter charge policy.
- **Ambient:** target 22 ± 1 °C, away from direct airflow/sunlight. Record ambient temperature and room conditions at start/end.
- **Screen:** use the same brightness percentage and refresh rate, record both, disable adaptive brightness, and keep display resolution and always-on settings constant.
- **Network:** use the same Wi-Fi access point, band, signal location, and traffic for networked scenarios. For offline tests enable airplane mode and keep radios identically disabled. Record signal strength and background sync state.
- **Background state:** reboot before a comparison block, wait 10 minutes at idle, then begin only after skin/battery temperatures return within 1 °C of the block's chosen starting value. Keep apps/services, notifications, and storage state consistent.
- **Workload:** document exact app/version, workload/scene, command or interaction steps, duration, foreground state, frame-rate cap, and expected I/O/network activity. Separate interactive, CPU, GPU, mixed, memory pressure, fixed storage I/O, camera/multimedia, idle-drain, suspend/resume, and charging workloads. Use a dedicated test path for I/O; do not overwrite personal data.

## Run procedure and statistics

1. Capture device metadata and a read-only idle snapshot. Record start charge, temperatures, CPU online set, governor/policy bounds, GPU policy, and thermal/cooling state.
2. For each workload, save a snapshot immediately before and after the timed interval. Sample high-rate time series only when needed and use the same sampling interval for all builds; avoid heavy polling that changes the workload.
3. Run at least five repetitions per condition. Randomize baseline/candidate order within a block where both kernels are installed. Reboot and use the same cooldown between runs; return to the starting temperature within 1 °C and charge band before each run.
4. Report every run, median, minimum/maximum, and interquartile range (or median absolute deviation). For frame pacing include frame-time distribution, 1% low FPS definition, missed/deadline frames, and a trace or raw frame-time file. A score alone is insufficient.
5. Monitor battery temperature and all accessible thermal zones through sustained runs. End the run on abnormal heating, unexpected throttling, instability, or charging behavior; do not adjust trips, cooling state, frequencies, or charging limits to force a result.
6. Capture timestamped kernel logs before and after each scenario and preserve the exact test order and environment. For storage runs retain queue attributes and diskstats deltas alongside userspace latency distributions; diskstats alone is not a latency measurement. Keep raw data, analysis script/version, and summarized results together.

## Suspend/resume procedure

With charging disconnected and radios/display conditions held constant, capture a pre-suspend snapshot and logs, request screen-off suspend through the same userspace procedure, and leave the device untouched for 30 minutes. Wake once with the same physical action; record time to usable display/input, wake source, suspend success/failure counters, elapsed time, battery/thermal change, and post-resume logs. Repeat five times. This observes end-to-end behavior; it does not isolate kernel wake latency without trace instrumentation.

## Data required

Required source nodes for CPU frequency/idle residency, online cores, KGSL/devfreq frequency and utilization, thermal/cooling devices, battery/charging, ZRAM, memory pressure, kernel logs, and suspend diagnostics are enumerated in [BUILD_BASELINE.md](BUILD_BASELINE.md). `scripts/xen-baseline/collect-device.sh` writes structured key/value metadata and a four-column TSV manifest with `collected`, `unavailable`, `permission_denied`, or `read_error` status. The collector is best-effort; inspect its manifest and supplement missing vayu interfaces manually.

## Measurement results

**None collected.** Physical-device capture remains pending on a rooted vayu device. VPS build logs, configuration, and benchmarks on another machine cannot stand in for device measurements.
