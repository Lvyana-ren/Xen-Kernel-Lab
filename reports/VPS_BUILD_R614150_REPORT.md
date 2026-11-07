# VPS Clang r614150 kernel build report

**Outcome: BLOCKED BEFORE TOOLCHAIN ACQUISITION; NO KERNEL BUILD WAS STARTED.** No successful or failed compiler exit status exists. No image or flashable ZIP exists. This report distinguishes that concrete environment blocker from a kernel/toolchain compile failure.

## Workspace/source identity

- Repository: `/home/xenlab/XenWorkshop/Xen-Kernel`
- Branch: `experiment/m0-m1-reproducible-baseline`
- HEAD/source commit: `1d7baee8d8363b1a1369bd1b3e654e30d5d5cc87`
- Tracked worktree changes are preserved and uncommitted. `git diff --binary HEAD | sha256sum`: `072248ef50f353647cff69f52e2f2d5758e037a1fe8dc6b44b67491ae8fedbd6`.
- Reports and `scripts/xen-baseline/collect-schedutil.sh` are untracked; no reset/clean/stash/revert/commit/push was performed.
- Baseline Clang r547379 checkout/toolchain is not installed in this execution environment. Its workflow selector remains the default and was not changed.

## Network diagnosis

Inspection time: 2026-11-07 09:23 UTC.

- `/etc/resolv.conf` resolves to `/run/systemd/resolve/stub-resolv.conf`, with `nameserver 127.0.0.53`.
- `/run/systemd/resolve/resolv.conf` lists upstream `8.8.8.8`.
- No HTTP(S)/ALL proxy variables were set.
- `getent ahosts android.googlesource.com` and `github.com` returned no addresses; `curl` to both official AOSP and GitHub failed with `Could not resolve host`.
- `systemctl`/`resolvectl status` cannot connect to systemd's bus; `ip route` cannot open netlink in this environment.
- `/proc/net/route` and `/proc/net/ipv6_route` show loopback entries only; `ens34` reports `up` but no non-loopback route is visible to this process.
- Direct `dig` to both the configured resolver and local stub fails before sending because socket creation returns `Operation not permitted`. Direct TCP socket tests fail with the same sandbox restriction.

This demonstrates the current execution sandbox blocks network sockets and does not expose a usable route. It does not establish whether the underlying host's physical network is down. No resolver, route, proxy, or systemd setting was changed; a local change would not remove the sandbox socket restriction. DNS/network repair requires running the acquisition/build in an environment with outbound sockets and a configured route or changing the execution policy externally.

## Toolchain acquisition

- Requested AOSP revision: `16fae8ef5b856b1d3e02a55274e4327c5842bb34`.
- Expected official package: clang-r614150 / LLVM 23.0.1.
- Archive URL: `https://android.googlesource.com/platform/prebuilts/clang/host/linux-x86/+archive/16fae8ef5b856b1d3e02a55274e4327c5842bb34/clang-r614150.tar.gz`.
- Download attempt could not proceed because network socket creation is denied. Archive SHA-256, acquisition timestamp, extracted path, Clang version, LLD version, target support, and executable status are **not available**. No substitute toolchain was used.
- `/home/xenlab/toolchains/` is outside this session's writable roots. The session can write only within the repository and `/tmp`; it did not create or write outside those allowed paths. Under current permissions the permissible temporary install location would be `/tmp/xen-toolchains/clang-r614150`.

## Effective vayu configuration preflight

Generated in `/tmp/xen-vayu-config.3h9me3/.config` and copied to `reports/VPS_PREBUILD_VAYU.config`.

- Config SHA-256: `7aef5933f1e0cfd82fd264573dbdf5ac5d9f508075c46e67e71db4e0964f59dc`.
- Config diff against `arch/arm64/configs/vayu_defconfig`: `reports/VPS_PREBUILD_CONFIG.diff`, SHA-256 `c52d859987ac7f65f6e18dd49a7287d10f93011d3ed6b0696bfdafb775b2a810`.
- Command: `make ARCH=arm64 O=/tmp/xen-vayu-config.3h9me3 vayu_defconfig`, apply the established workflow's release/ThinLTO/performance and experiment-off settings using `scripts/config`, then `make ARCH=arm64 O=/tmp/xen-vayu-config.3h9me3 olddefconfig`.
- Verified: `CONFIG_MACH_XIAOMI_VAYU=y`, WALT, SchedTune, KGSL, ZRAM, schedutil, `CONFIG_LOCALVERSION="-Xen+3"`, `CONFIG_LTO=y`, `CONFIG_LTO_CLANG=y`, `CONFIG_THINLTO=y`, `CONFIG_CC_OPTIMIZE_FOR_PERFORMANCE=y`.
- CPU-001, CPU-002, and MEM-002 are disabled; LZ4HC is disabled. This is configuration-only evidence, not a compiler or kernel build.

## Installed build prerequisites

Present: make, Python 3, Perl, Git, `bc`, GCC host compiler, OpenSSL development headers, zlib development headers, rsync, ZIP/unzip.

Missing: clang, ld.lld, LLVM binutils, bison, flex, AArch64 cross GCC/binutils, ARM32 cross GCC/binutils, dtc, ccache, libelf development headers, and ncurses development headers. Apt package metadata shows corresponding packages are not installed. No packages were installed because outbound network and system package modification are unavailable in this execution environment.

VPS-visible capacity: 4 logical CPUs, 9.7 GiB RAM with 8.7 GiB available at inspection, 4 GiB swap with about 3 GiB used, 103 GiB free on the source filesystem. Use two build jobs after provisioning to limit OOM risk.

## Build inputs and status

Intended comparison: same full reviewed source tree, release Xen+3, vayu defconfig, CPU experiment baseline, memory experiment baseline, same ThinLTO/performance config; only compiler changes from r547379 to r614150. Actual pair: **not run**.

Planned target command after toolchain/dependencies are available (build from an isolated reviewed source copy with the existing exact M0 patches applied):

```sh
PATH=/home/xenlab/toolchains/clang-r614150/bin:$PATH \
make -j2 O=out-r614150 ARCH=arm64 SUBARCH=arm64 \
  DTC_EXT=dtc CLANG_TRIPLE=aarch64-linux-gnu- \
  CROSS_COMPILE=aarch64-linux-gnu- \
  CROSS_COMPILE_ARM32=arm-linux-gnueabi- \
  CROSS_COMPILE_COMPAT=arm-linux-gnueabi- \
  CC='ccache clang' LD=ld.lld AR=llvm-ar NM=llvm-nm \
  STRIP=llvm-strip OBJCOPY=llvm-objcopy OBJDUMP=llvm-objdump \
  READELF=llvm-readelf HOSTCC=clang HOSTCXX=clang++ \
  HOSTAR=llvm-ar HOSTLD=ld.lld LLVM=1 LLVM_IAS=1 Image
```

Do not run the command until the toolchain is actually installed and the source copy/config is prepared. The current checkout has dirty, uncommitted source changes and the workflow-only patches are not applied to the source tree; HEAD alone is not a complete identifier for the intended build state.

## Build outputs

- Build status: **NOT STARTED / BLOCKED**, not a compiler failure.
- First meaningful blocker: `Operation not permitted` when this process attempts to create a network socket; host lookup fails; the AOSP archive and required toolchains cannot be acquired.
- Kernel `Image`: none.
- Kernel release: none generated by build.
- Build log / duration / peak RSS: none.
- Image SHA-256/size: none.
- Requested ZIP `artifacts/Xen-Kernel-Lab-vayu-Clang-r614150.zip`: not created.
- Termux download command: unavailable until a verified artifact exists and is hosted at a reachable path.

## Next actions

1. Run this same preserved working tree in an execution environment with outbound DNS/TCP sockets and the system package installation permission required for missing dependencies.
2. Download only the pinned AOSP archive, record its SHA-256, verify tar integrity, `AndroidVersion.txt`, Clang/LLD versions and target support, and install it without touching r547379.
3. Prepare an isolated source copy containing this reviewed worktree state and the two checked M0 patches; record a digest for the dirty diff.
4. Build baseline config with two jobs, preserving ThinLTO and performance optimization. Record compiler output, real exit code, release, image SHA, duration and resource usage. Only package a vayu AnyKernel ZIP if an established compatible AnyKernel3 tree is present and can be verified; otherwise provide a raw kernel artifact without inventing a flasher.
5. Build r547379 with exactly matched inputs if that toolchain can also be made available, then conduct device validation before any performance claim.
