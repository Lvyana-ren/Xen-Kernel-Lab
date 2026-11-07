# Device validation required

## External blocker

No Poco X3 Pro (vayu), rooted Android session, ADB/fastboot binary, or device transport is available in this VPS session. No device results are inferred from source. Do not call the mission complete until this validation is performed on actual hardware.

## Before measuring

1. Publish or obtain the exact experiment commit and record full SHA. Build it with Actions and verify artifact hashes, patch list and final config.
2. Use a known-good recovery/boot image and reversible install path. Record current boot image/DTB, ROM build, root manager and recovery route before testing.
3. Confirm `ro.product.device=vayu`, kernel release, ROM fingerprint, SELinux state and boot slot. Preserve baseline image and rollback instructions.
4. Use `scripts/xen-baseline/collect-device.sh` via `DEVICE_BASELINE_GUIDE.md`. Never write sysfs/procfs tuning values as part of capture.
5. Follow controlled conditions in `RUNTIME_BASELINE.md`: battery bands, ambient temperature, brightness/refresh, network state, idle/cooldown, same app/build and at least five repetitions.

## Required scenarios

- Idle screen-on and screen-off residency; suspend for 30 minutes, five cycles, record suspend failures/wake sources and wake-to-usable time.
- Interactive workload: consistent UI interaction and app launch; capture pre/post policy/thermal snapshots and targeted sched_waking/wakeup/switch trace only in separate instrumented runs.
- Gaming: same game build, scene, frame cap, graphics settings, display state and network; capture raw frame timestamps/Perfetto or game frame metrics, GPU utilization/frequency, CPU time-in-state and temperatures.
- CPU sustained load: fixed workload duration and throughput; record frequency/online/thermal state throughout, not only peak score.
- Memory pressure: controlled allocation/reclaim workload; capture PSI, vmstat, zram mm_stats/compressor/swap and workload latency. Do not induce OOM or modify memory controls.
- Storage: fixed read/write workload on the same storage location; capture queue scheduler/limits and diskstats deltas; use userspace latency histograms. Avoid writing test data to user filesystems without a dedicated test location.
- Mixed CPU/GPU gaming sustained block: correlate frame pacing, CPU/GPU residency, cooling states, skin/battery temperature and energy/current.

## Analysis and acceptance

Keep each raw run and exact test environment. Report median, IQR or MAD, p95/p99 latency where applicable, worst run, temperature trajectory and battery/energy change. Compare baseline and candidate in randomized order. Separate traced and untraced runs. Reject any change that trades sustained thermals, battery life, stability, suspend or background responsiveness for a short benchmark score.

Technical lead must review results and rollback readiness before any production promotion. No device baseline currently exists.


## Schedutil experiment capture addition

For each baseline, CPU-002, and CPU-001 run, use `scripts/xen-baseline/collect-schedutil.sh <run-label> before|during|after <output.tsv>` and preserve the appended TSV with the raw run. Record all policy rows, statuses, and timestamps; specifically compare `up_rate_limit_us` and `down_rate_limit_us` without writing either node. The script also records policy CPU membership, governor, current frequency, available frequency list, min/max limits, and transition latency. A missing or permission-denied row is evidence to report, not a value to fill in. See the CPU experiment reports for exact invocation and interpretation.


## MEM-002 validation

For baseline and LZ4HC builds, verify the active runtime algorithm from `/sys/block/zram0/comp_algorithm` before initializing test swap; record userspace writes/configuration that may override the kernel initial default. Preserve raw `disksize`, `max_comp_streams`, `mm_stat`, `io_stat`, PSI, vmstat and workload logs before/after each run. Compare randomized paired memory-pressure repetitions for CPU consumption, allocation/reclaim latency, app responsiveness, energy and temperature. Keep ZRAM size, swap policy, workload, starting state and ambient/display conditions matched. Do not write compressor or size sysfs nodes as part of collection.
