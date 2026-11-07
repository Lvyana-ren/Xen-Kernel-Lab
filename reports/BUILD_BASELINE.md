# Build baseline collection specification

Target: Poco X3 Pro (`vayu`, Qualcomm SM8150), Linux 4.14.357.

## CI/VPS data

`.github/workflows/build-kernel.yml` accepts an explicit `source_ref` dispatch input (branch name or commit SHA, default `16`) and fails if the checked-out SHA does not resolve to that requested source. It records source identity separately from the workflow trigger ref/SHA. Release flavor (`xen` or `ksun`) and positive release generation are explicit inputs.

The workflow artifacts capture source/ref validation; requested source ref, checked-out source SHA and workflow trigger ref/SHA; original source SHA; toolchain Git SHA and deterministic tree SHA256; Clang/LLD and cross compiler/binutils/Make versions; runner OS/image metadata; timestamps; effective `.config`; config validation; generated `kernel.release` and release validation; verbose build log including actual Clang, `-flto=thin`, and LLD invocation evidence; `Image` SHA256/size; ccache stats; exact build patch files and patch SHA256 values; applied-patch list/status; post-patch source diff; untracked generated-file list/archive; worktree status; artifact checksum manifest; and `mutable-dependencies.txt` with runner/action/apt dependency declarations and installed Debian package versions. Artifact retention is configured for 30 days. The resolved Clang branch commit and tree hash are recorded, but its upstream SHA is not yet fixed.

The generated workflow release is validated against `4.14.357-Xen+N` or `4.14.357-Xen-KSUN+N`. The experiment branch includes an exact-context patch that changes only `EXTRAVERSION = -openela` to an empty value and fails if the source context differs. `LOCALVERSION_AUTO` is disabled to prevent an implicit Git suffix; the requested generation is supplied as `LOCALVERSION`, and the complete generated string is checked against the requested flavor/generation.

The build applies a separate exact-context patch adding `<linux/cpu.h>` to `hyp_core_ctl.c` because the file references `cpu_subsys`, declared in that header. It verifies both source use and declaration before applying. ZRAM already defaults to LZ4 in tracked source; the workflow now verifies that value and does not edit the implementation. `CONFIG_ZRAM=y` is in vayu defconfig; this tree has no Kconfig symbol for selecting the compressor.

Kconfig here defines `THINLTO`, dependent on `LTO_CLANG` and architecture support. It does not define `LTO_CLANG_THIN`. The workflow enables and validates `CONFIG_LTO=y`, `CONFIG_LTO_CLANG=y`, `CONFIG_THINLTO=y`, and `CONFIG_CC_OPTIMIZE_FOR_PERFORMANCE=y` after `olddefconfig`, then checks build log evidence for `-flto=thin` and `ld.lld`. This verifies build configuration and invocation, not runtime performance.

CI still uses a mutable Clang source branch (`15.0`) and Ubuntu hosted image label (`ubuntu-22.04`), while recording the resolved toolchain commit/tree hash and available runner image details. Apt package versions are not locked. These are remaining reproducibility limits; no compiler version or optimization decision was changed.

## Physical device only

Build artifacts and VPS metadata cannot establish device runtime behavior. Physical vayu collection must use the exact kernel image, merged device tree and userspace under test. Record model/codename, fingerprint/ROM, kernel release, build SHA, root state, ambient temperature, battery age/health, date, workload and charge state.

The read-only `scripts/xen-baseline/collect-device.sh` writes `metadata.txt`, per-node snapshots and a four-column `manifest.tsv` status inventory. It records `collected`, `unavailable`, `permission_denied`, or `read_error` and does not treat missing interfaces as zero. Rooted Android sysfs/debugfs layout varies; review the manifest and supplement vayu-specific nodes. `XEN_BASELINE_TEST_ROOT` enables mock-node testing on a host.

## Runtime fields to collect

| Area | Data |
|---|---|
| CPU | Online/possible/present CPUs; per-CPU and policy governor, driver, available/current/min/max frequency, policy masks, time in state, transition latency; cpuidle names/latency/time/usage; scheduler sysctls, core_ctl state and tunables. |
| GPU | KGSL/devfreq name, available/current frequency, governor, utilization/busy counters and idle/power state where exposed. |
| Thermal | Zone type/name, temperature, trip metadata and all cooling-device types/current/max state. Read only. |
| Battery/charging | Temperature, voltage/current, capacity/charge counter, status/health, input/current limit metadata and connected source. Do not change settings. |
| Memory | `/proc/meminfo`, `/proc/vmstat`, `/proc/zoneinfo`, PSI where present, `/proc/swaps`, ZRAM compressor/size/mm and I/O stats. |
| Storage/I/O | `/proc/diskstats`, `/sys/block/*/stat`, queue scheduler, read-ahead, request count, rotational and timeout attributes where present. These are snapshots/cumulative counters; userspace latency histograms are still required. |
| Runtime | Timestamped kernel logs, wakeup sources, suspend stats/failures and trace events in a separate controlled trace run. |

## VPS versus device

VPS can collect source and workflow identity, config, release metadata, toolchain and runner details, build logs, image hashes and source modifications. Only the physical target can provide CPU/GPU residency, device temperatures, charging current, suspend behavior, frame pacing, latency and battery-use measurements.
