# Memory, ZRAM and storage source research

## Memory and reclaim

`vayu_defconfig` enables swap, memory cgroups and memcg swap. Linux 4.14 reclaim is implemented primarily in `mm/vmscan.c`: direct reclaim enters page/zone/node scan paths; kswapd performs background reclaim; shrinkers and LRU aging can add latency and CPU work under pressure. Relevant observations include `/proc/meminfo`, `/proc/vmstat`, `/proc/pressure/*` if implemented, `/proc/zoneinfo`, swap stats and allocation/reclaim trace events. A source configuration alone does not show pressure on the target.

## ZRAM

Defconfig enables `CONFIG_ZRAM=y` and `CONFIG_ZSMALLOC=y`; deduplication and writeback are disabled. `drivers/block/zram/zram_drv.c` sets the source default compressor to LZ4. This is an implementation default; no compressor selection exists in this tree's ZRAM Kconfig or generated config. Runtime userspace may select another compressor or size. The collector records ZRAM size, algorithm and mm/io stats when exposed. Preserve this runtime state before considering changes.

Potential trade-off: a different compressor may reduce stored bytes but increase CPU time and heat, or may compress faster while using more memory. No compressor, swap priority, zram size or reclaim parameter was changed. The default is not an experimentally proven optimum for vayu workloads.

## CMA and LLCC

Defconfig contains CMA with `CONFIG_CMA_SIZE_MBYTES=16` and seven areas. This alone does not establish pressure: multimedia clients and merged device-tree reservations determine demand. SM8150 DTS describes LLCC hardware and performance monitor support; cache slice setup and bandwidth votes are driver/client/firmware coordinated. Do not change CMA or LLCC without allocation-failure, reclaim, bandwidth and multimedia measurements.

## Storage and block layer

The defconfig compiles noop, deadline and CFQ plus multi-queue deadline and Kyber. This does not select the runtime queue scheduler on each UFS/block device; Android fstab, kernel block-device registration and userspace policy determine what is active. The read-only collector now records `/proc/diskstats`, `/sys/block/*/stat`, queue scheduler, read-ahead, request count, rotational and timeout attributes where present. These are cumulative counters/config snapshots, not latency distributions. Use a controlled userspace I/O workload with latency histograms to test tails.

## Decision

No memory, compression, CMA, LLCC, block scheduler or queue optimization is accepted without actual vayu pressure/latency evidence. No memory or storage runtime parameter was tuned.

## Follow-up source/config review — 2026-11-07

Confirmed `CONFIG_ZRAM=y`, `CONFIG_ZSMALLOC=y`, LZ4 in `zram_drv.c`, and ZRAM deduplication/writeback disabled in `vayu_defconfig`. The tree exposes `mm_stat` and compression/runtime statistics where enabled, but runtime userspace can select the active algorithm and configure swap. The defconfig also enables PSI and compaction, CMA 16 MiB with seven areas, and noop/deadline/CFQ plus MQ deadline/Kyber; none identifies the active vayu block scheduler or current pressure. No M5 experiment is justified until runtime ZRAM algorithm/statistics, PSI/vmstat, reclaim events, allocation/CMA pressure and controlled I/O latency are captured.


## Follow-up experiment — MEM-002

Added an opt-in LZ4HC initial-compressor candidate. `drivers/block/zram/zram_drv.c` selects `lz4hc` only under `CONFIG_XEN_EXPERIMENT_ZRAM_LZ4HC_DEFAULT`; the normal config remains LZ4. `drivers/block/zram/Kconfig` defaults the experiment off and selects `CRYPTO_LZ4HC` only when requested. Workflow input `memory_experiment` validates and records the choice, and forbids combining it with a non-baseline CPU variant. Local baseline and experimental `olddefconfig` outputs confirm respectively no experiment/HC backend and experiment plus `CONFIG_CRYPTO_LZ4HC=y`. This is **implemented and statically validated only**. No build or runtime result exists. See `MEM_EXPERIMENT_MEM-002.md` for matched test and rollback criteria.
