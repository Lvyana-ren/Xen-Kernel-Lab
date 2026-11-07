# AOSP clang-r614150 toolchain review

## Decision and status

**AOSP release identity verified from official source; toolchain NOT acquired locally; build NOT run.** The Android Clang prebuilts README identifies clang-r614150 (LLVM 23.0.1) as current for Android platform and mainline-kernel users. The release change is pinned to AOSP commit `16fae8ef5b856b1d3e02a55274e4327c5842bb34` in `platform/prebuilts/clang/host/linux-x86`.

Official references:

- AOSP prebuilts repository and version table: https://android.googlesource.com/platform/prebuilts/clang/host/linux-x86/
- Exact r614150 update commit: https://android.googlesource.com/platform/prebuilts/clang/host/linux-x86/+/16fae8ef5b856b1d3e02a55274e4327c5842bb34
- AOSP main-kernel mirror integration also lists r614150: https://android.googlesource.com/platform/prebuilts/clang/host/linux-x86/+/refs/heads/main-kernel/

## Acquisition identity

- Official project: `https://android.googlesource.com/platform/prebuilts/clang/host/linux-x86`
- Pinned archive URL: `https://android.googlesource.com/platform/prebuilts/clang/host/linux-x86/+archive/16fae8ef5b856b1d3e02a55274e4327c5842bb34/clang-r614150.tar.gz`
- Pinned source commit: `16fae8ef5b856b1d3e02a55274e4327c5842bb34`
- Version declared by AOSP: clang-r614150 / LLVM 23.0.1.
- Local archive SHA-256: **not available**; the VPS could not resolve `android.googlesource.com` (`curl: (6) Could not resolve host` against both `android.googlesource.com` and the official alternate `android.git.googlesource.com`). No archive was downloaded (attempted 2026-11-07 09:08 UTC; DNS failure), so no local acquisition timestamp, binary version output, LLD output, or archive checksum is claimed.
- Expected installation location if acquisition is retried under the current filesystem permissions: `/tmp/xen-toolchains/clang-r614150`. `/opt` and home toolchain directories are not writable under this environment's workspace permissions.

The pinned Git commit plus HTTPS endpoint identifies the intended source. A successful acquisition must run `tar -tzf`/extract validation and record SHA-256. AOSP does not publish an archive SHA in the checked source; the workflow records the computed archive hash and verifies gzip/tar integrity and the extracted clang/LLD versions. This hash is provenance for that acquired archive, not a comparison against an independently published checksum.

## Workflow integration

`.github/workflows/build-kernel.yml` now has a `toolchain` workflow-dispatch choice:

- Default `clang-r547379`: existing GitLab clone/ref path is retained.
- `clang-r614150`: fetches the pinned AOSP archive to the runner temp directory, computes its SHA-256, extracts outside the source tree, verifies Clang and LLD report 23.0.1, verifies all LLVM binaries exist, and puts only the selected toolchain's `bin` directory first in `PATH`.

The common validation step ensures `clang`, `clang++`, `ld.lld`, `llvm-ar`, `llvm-nm`, `llvm-strip`, `llvm-objcopy`, `llvm-objdump`, and `llvm-readelf` resolve inside the selected toolchain. Existing AArch64/ARM32 GCC cross compilers remain separate and are not LLVM utilities. Artifact provenance records selector, source, archive URL/hash, AOSP commit, toolchain tree hash, compiler/linker versions, source SHA, and selected CPU/memory experiments. Existing defaults for toolchain, source, release, CPU experiment, and memory experiment remain unchanged.

## Compatibility assessment

AOSP listing for Android mainline kernels is evidence that this is a supported Android kernel toolchain, but it does not prove compatibility with this downstream Linux 4.14.357 tree, its ThinLTO integration, its legacy build scripts, or this Android 12-era platform code. Compatibility is **unknown until an actual build**. Keep r547379 as the comparison baseline. Do not disable ThinLTO, reduce optimization, or alter source to hide compatibility failures. Fix only specific diagnosed incompatibilities and preserve all logs.

## VPS constraints and actual status

At review, the VPS reports 4 logical CPUs, 9.7 GiB RAM, 8.7 GiB available, and 4 GiB swap with about 3 GiB in use. The source filesystem has about 103 GiB free. `clang`, `ld.lld`, AArch64/ARM32 cross GCC, `dtc`, and `ccache` are unavailable. DNS lookup for the official AOSP host fails. A conservative future local build should use two parallel jobs, separate `O=` directories per toolchain, and monitor memory/peak RSS. Neither matched build could be started here.

## Remaining checks

1. Restore DNS/network access to `android.googlesource.com` (the `android.git.googlesource.com` alternate also failed resolution).
2. Download the exact pinned archive outside the kernel tree, record acquisition UTC and SHA-256, inspect archive integrity, `AndroidVersion.txt`, `clang --version`, and `ld.lld --version`.
3. Compare the extracted toolchain tree hash and retain the archive checksum in provenance.
4. Build identical source/config/release/experiment inputs under r547379 and r614150. Preserve ThinLTO and `CONFIG_CC_OPTIMIZE_FOR_PERFORMANCE`.
5. Review all warnings/errors and resulting images before deciding whether r614150 is suitable for further experiments.
6. Physical boot, stability, battery, thermal, and performance testing on vayu remains required; compiler version alone proves no performance improvement.

For retry, restore DNS first, then install the workflow dependencies (`bc bison build-essential ccache flex git curl libelf-dev libssl-dev make python3 rsync device-tree-compiler gcc-aarch64-linux-gnu gcc-arm-linux-gnueabi binutils-aarch64-linux-gnu binutils-arm-linux-gnueabi libncurses-dev lz4 zip wget xz-utils file`). Keep toolchains under `/tmp/xen-toolchains/`, and use two build jobs on this 4-CPU/10-GiB VPS to limit memory pressure. The updated workflow AOSP archive URL and checks are the canonical acquisition procedure; no unverified local download command was substituted.
