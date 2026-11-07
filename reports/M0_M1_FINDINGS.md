# M0/M1 findings summary

This summary points to the detailed acceptance review in [M0_HARDENING_REVIEW.md](M0_HARDENING_REVIEW.md). It supersedes the earlier source-ref and collector limitations recorded in the initial M0 note.

## M0

- Workflow accepts explicit source ref and validates its resolved SHA; input defaults to branch `16` and can select an experiment branch or commit SHA.
- ThinLTO option in this tree is `CONFIG_THINLTO`, not `CONFIG_LTO_CLANG_THIN`. The workflow configures/checks LTO, Clang LTO, ThinLTO and performance optimization after `olddefconfig`; verbose build output is checked for `-flto=thin` and `ld.lld`.
- Workflow records source/workflow identity, toolchain commit and tree checksum, compiler/linker versions, runner metadata, timestamps, final config/release, config/release validation, image hash/size, build log, ccache and tracked/untracked source mutations.
- Release normalization is represented by an exact-context patch that only changes the known `EXTRAVERSION=-openela`; workflow fails on other source values and validates full Xen/Xen-KSUN release against flavor and generation.
- M0 not fully closed until CI is run manually by an authorized operator and artifact outputs are reviewed. Codex did not dispatch Actions or run a full build.

## M1

- Collector is read-only with structured metadata and TSV manifest; it distinguishes missing, permission-denied and read-error nodes. It gathers CPU online/isolated/nohz topology, frequency/idle/core_ctl, common schedtune scalar files, KGSL/devfreq, thermal, power supply, memory/ZRAM, block queue/diskstats, suspend metadata and dmesg where readable.
- Shell syntax and mock-node behavior were validated locally, including new CPU/schedtune/storage paths and missing-node reporting. Physical collection remains pending on a rooted Poco X3 Pro; live sysfs availability and permissions are unknown.
- Runtime test conditions and result separation are documented in `RUNTIME_BASELINE.md`; there are no measured results.

## M2

CPU source analysis is in [CPU_RESEARCH.md](CPU_RESEARCH.md), with GPU, memory/storage, thermal/power, gaming/latency and security/stability reports added. The analysis identifies the configured Qualcomm stacks and their interactions. All performance candidates remain hypotheses pending device evidence.
