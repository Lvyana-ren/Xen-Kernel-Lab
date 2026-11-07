# MEM-002 — opt-in ZRAM LZ4HC initial-compressor comparison

**State:** IMPLEMENTED; effective configuration statically validated; NOT BUILT; NOT DEVICE VALIDATED; NOT MEASURED; NOT ACCEPTED.

## Hypothesis

Compared with the existing LZ4 initial default, LZ4HC may reduce compressed ZRAM footprint for vayu workloads at the cost of additional compression CPU time and energy. This is a falsifiable trade-off, not a claim of better performance. Measure compression ratio, CPU use, reclaim/swap latency, application responsiveness, energy, and thermals under the same memory pressure workload.

## Source and implementation

- `drivers/block/zram/zram_drv.c`: compile-time selection sets `default_compressor` to `lz4hc` only when `CONFIG_XEN_EXPERIMENT_ZRAM_LZ4HC_DEFAULT=y`; otherwise it remains `lz4`.
- `drivers/block/zram/Kconfig`: new opt-in bool defaults to `n`, depends on ZRAM and existing LZ4 crypto support, and selects `CRYPTO_LZ4HC`.
- `.github/workflows/build-kernel.yml`: new `memory_experiment` dispatch input defaults to `baseline`; `zram_lz4hc_default` enables the Kconfig symbol, validates it and `CONFIG_CRYPTO_LZ4HC` after `olddefconfig`, and archives the selected label. The workflow rejects simultaneous non-baseline CPU and memory experiments to prevent confounded variants.
- The compressor implementation, runtime sysfs interface, ZRAM size, swap policy, writeback, deduplication, and thermal behavior are not changed. Android userspace may override the initial compressor before device initialization; capture `/sys/block/zram0/comp_algorithm` after boot and during tests.

## Risk and acceptance

Main risk: LZ4HC can increase compression latency and CPU energy; any memory savings can be offset by compute costs. Kernel default only applies when userspace does not override it. Accept only if repeated matched tests show a useful memory-pressure benefit without worse latency, energy, temperature, app stability, or sustained behavior. Otherwise reject and retain baseline LZ4. Rollback is selecting `memory_experiment=baseline`; source default remains LZ4 when the symbol is off.

## Validation

Local `vayu_defconfig` plus `olddefconfig` resolved baseline with the experiment unset and `CRYPTO_LZ4HC` absent; the experimental configuration resolved the symbol and `CONFIG_CRYPTO_LZ4HC=y`. Workflow YAML parsed, embedded Bash passed `bash -n`, and `git diff --check` passed. No compile or CI run was performed. Runtime compressor state and all performance/energy outcomes require rooted vayu tests.

## Device protocol

Use the same source SHA and toolchain for baseline and LZ4HC builds. Before workload initialization, record actual `comp_algorithm`, `disksize`, `max_comp_streams`, `mm_stat`, `io_stat`, `/proc/vmstat`, PSI, and memory state. Run at least five randomized paired memory-pressure repetitions from matched battery/thermal/cooldown conditions. Preserve raw snapshots and workload latency/throughput. Report compression ratio and CPU time/energy alongside reclaim, app response, and temperature; do not write ZRAM sysfs in the collector or baseline procedure.
