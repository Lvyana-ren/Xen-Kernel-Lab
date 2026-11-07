# Build validation report

## Repository and workflow state

- Branch: `experiment/m0-m1-reproducible-baseline`
- HEAD: `1d7baee8d8363b1a1369bd1b3e654e30d5d5cc87`
- At initial inspection, `HEAD` matched `origin/experiment/m0-m1-reproducible-baseline`; worktree was clean.
- Baseline source parent: `bf6ac1247feda28293062995d445506b050aec8a` (`origin/16`). Changes between the source parent and experiment HEAD are only workflow, patch files, and collector, not CPU/GPU/memory/thermal driver source.
- GitHub Actions read-only run query returned zero runs on the experiment branch. The available GitHub integration exposes fetch/read operations, not workflow dispatch. No `gh`, clang, or ld.lld executable is installed in the VPS; no ADB device is attached.

## Static/build evidence

M0 workflow accepts source ref, release flavor and positive generation; verifies source ref against `HEAD`; applies exact-context patches; validates LTO config after olddefconfig; validates final release naming; compiles verbose and requires `-flto=thin` and LLD evidence; captures config, source/patch provenance and checksums. Artifact retention is 30 days. Clang 15.0 branch, Ubuntu 22.04 runner, apt packages and Actions v4 tags are mutable dependencies, though resolved toolchain and package metadata are captured.

Static validation performed in this mission: workflow YAML parse, embedded Bash parse, collector shell parse, patch applicability/idempotence, source/config fact review and git diff whitespace checks. Collector mock test is recorded with the mission changes. The CPU-001 config variant was additionally checked through `vayu_defconfig` plus `olddefconfig` in an out-of-tree `/tmp` output directory: the experiment symbol resolves on when selected and off for baseline, while schedutil remains enabled. This is not a kernel build.

## Result

**Build status: NOT RUN.** No successful or failed kernel build can be claimed. No build artifact or image checksum exists for the current branch. Use the GitHub Actions manual dispatch after publishing current changes with `source_ref=experiment/m0-m1-reproducible-baseline`, `release_flavor=xen`, and `release_generation=3`. Review `source-validation.txt`, `original-source-sha.txt`, `applied-patches.txt`, patch hashes, `post-patch-source.diff`, `kernel.config`, `kernel-release.txt`, ThinLTO build evidence, Image SHA256, and artifact checksum manifest.

## CPU-001 build variant

The workflow now accepts `cpu_experiment=baseline` (default) or `sugov_no_rate_limit`. Both variants retain ThinLTO and the same compiler/toolchain inputs. The experiment config enables `CONFIG_XEN_EXPERIMENT_SUGOV_NO_RATE_LIMIT`, which sets schedutil's initial up/down rate limits to zero; the baseline config explicitly disables it. `config-validation.txt` and `cpu-experiment.txt` record the selected variant, and `kernel.config` captures its effective configuration. Neither variant has been built in this environment.

## CPU-002 build variant and current validation

The workflow additionally accepts `cpu_experiment=sugov_no_up_rate_limit`; it sets only `CONFIG_XEN_EXPERIMENT_SUGOV_NO_UP_RATE_LIMIT` and preserves schedutil's driver-derived downward rate limit. Kconfig makes the variants mutually exclusive. `vayu_defconfig` plus `olddefconfig` was run separately for baseline, CPU-002-only and CPU-001-only settings; all resolved as expected. During this check, Kconfig omitted the CPU-002 symbol when its dependency was false; the workflow was corrected to reject only an actually enabled conflicting symbol rather than requiring an explicit `# ... is not set` line. Workflow YAML parsed, all embedded Bash blocks passed `bash -n`, and `git diff --check` passed. No kernel compile or Actions workflow run was possible: this environment has no Clang/LLD or `gh`, the workflow edits are uncommitted, and no workflow-dispatch operation is available through the connected GitHub tools.

The next build must run the same source commit/toolchain in three Actions dispatches with `source_ref` set to the published experiment branch and `release_flavor=xen`, `release_generation=3`; select respectively `baseline`, `sugov_no_up_rate_limit`, and `sugov_no_rate_limit`. Compare `kernel.config`, `config-validation.txt`, `cpu-experiment.txt`, release, build logs, image checksums and ccache/toolchain provenance. This is build preparation, not build evidence.

## Matched CPU-001/CPU-002 build comparison

The workflow's `cpu_experiment` dispatch input selects exactly one of `baseline`, `sugov_no_up_rate_limit`, or `sugov_no_rate_limit`; it explicitly disables the other experiment symbol, runs `olddefconfig`, and fails if the selected symbol is absent or a conflicting symbol is enabled. The selected label is included in `config-validation.txt` and `cpu-experiment.txt`; `.config` is saved as `kernel.config` in each run's artifacts.

After the operator publishes the current worktree, run three manual workflow dispatches using the **same full source commit SHA**, release flavor `xen`, generation `3`, and unchanged toolchain inputs. Select one experiment value per run. Compare artifacts by workflow run ID because the artifact display name is the same per run. Verify source SHA, toolchain commit and tree hash, runner/dependency provenance, `CONFIG_XEN_EXPERIMENT_*` state, ThinLTO/performance config, generated release and Image SHA256. This establishes matched build/config evidence only; it does not validate boot or runtime values. Then collect active sysfs tunables before/during/after each physical-device experiment with `collect-schedutil.sh`. Do not write values to make a run match its expected config.

Collector validation in this worktree: `sh -n` passed. Temporary mocks exercised per-policy and global tunable layouts, active schedutil and non-schedutil policies, missing nodes, before/during/after labels, nine-column TSV output, the pseudo-filesystem output guard, and a simulated permission-denied read. This is not a physical vayu capture.


## Validation checkpoint — 2026-11-07

Fresh local validation passed: baseline/CPU-001/CPU-002 `vayu_defconfig` plus `olddefconfig` selection checks; workflow YAML parse and dispatch choice/default review; embedded Bash `bash -n`; `sh -n` for device and schedutil collectors; `git diff --check`. Collector mock cases are documented in the CPU reports. No full build was attempted, no workflow was dispatched, and no artifacts/logs exist. `clang`, `ld.lld`, `gh`, and ADB/fastboot are absent. The changed workflow/report worktree must be published by an operator before hosted Actions can validate it. Release candidate status: **NOT PREPARED** (`RELEASE_CANDIDATE_REPORT.md`).


## MEM-002 variant preparation

Added workflow `memory_experiment` with `baseline` default and `zram_lz4hc_default` candidate. Workflow rejects simultaneous non-baseline CPU and memory experiment selection, applies the config before `olddefconfig`, checks the opt-in symbol and `CONFIG_CRYPTO_LZ4HC`, and records `memory-experiment.txt` in artifacts. Local vayu baseline config retained LZ4 with experiment/HC backend off; experimental config enabled the Xen option and HC backend. Workflow YAML and embedded Bash syntax passed. No kernel compile or hosted Actions run occurred. For an isolated M5 comparison, dispatch the same full source SHA and toolchain twice, with CPU experiment `baseline`, memory experiment `baseline` then `zram_lz4hc_default`; do not combine it with CPU-001/002. Runtime userspace may overwrite the initial compressor, so build config alone is not sufficient evidence.


## Clang r614150 integration / direct VPS build checkpoint — 2026-11-07

Added a `toolchain` workflow-dispatch input with unchanged default `clang-r547379` and new option `clang-r614150`. The experimental option downloads the official AOSP archive from the pinned r614150 update commit, computes and records its SHA-256/acquisition time, validates the archive by extraction and the actual Clang/LLD version strings, checks all required LLVM utilities, and verifies they resolve from one selected toolchain directory. The baseline GitLab clone path remains separate and unchanged. The build's existing source, release, CPU/memory experiment inputs, ThinLTO and optimization choices remain intact.

Official AOSP metadata identifies clang-r614150 as LLVM 23.0.1 and lists it for Android mainline kernel use; this does not prove Linux 4.14 compatibility. Direct acquisition failed: `curl` returned `Could not resolve host: android.googlesource.com`. This VPS has 4 logical CPUs, 9.7 GiB RAM (8.7 GiB available at inspection), 4 GiB swap with about 3 GiB used, and 103 GiB free on the source filesystem. `clang`, `ld.lld`, AArch64/ARM32 cross GCC, `dtc`, and `ccache` are absent. No baseline or experimental compiler could be used. No build was attempted; no image, kernel release, final toolchain build config, log, checksums, resource record, or ZIP exists.

Validation performed after the integration: workflow YAML parsed and the toolchain selector/defaults were asserted; every embedded workflow Bash block passed `bash -n`; `git diff --check` passed. No compiler invocation or build check was possible. The actual archive SHA, local build result, compiler compatibility, and paired configuration comparison remain pending network/toolchain access. Keep `-j2` as the conservative direct VPS build setting when dependencies are available, and use separate output directories for the two compilers.


## VPS Clang r614150 build attempt — 2026-11-07

A read-only network diagnosis found `/etc/resolv.conf` pointing to the systemd stub at `127.0.0.53`; `/run/systemd/resolve/resolv.conf` lists upstream `8.8.8.8`. No proxy variables are configured. Host lookups for both AOSP and GitHub failed. `systemctl`/`resolvectl` and `ip route` cannot access the system bus/netlink in this execution sandbox; `/proc/net/route` shows only loopback routes. Direct DNS/TCP socket creation is denied with `Operation not permitted`, so this is an execution sandbox networking restriction; the underlying VPS host's network state cannot be fully queried or repaired from here. No host networking setting was changed.

The current effective vayu preflight `.config` was generated with `vayu_defconfig`, Xen+3 localversion, established ThinLTO/performance settings, CPU and memory experiments disabled, then `olddefconfig`. It is saved as `reports/VPS_PREBUILD_VAYU.config` (SHA-256 `7aef5933f1e0cfd82fd264573dbdf5ac5d9f508075c46e67e71db4e0964f59dc`); its defconfig comparison is `reports/VPS_PREBUILD_CONFIG.diff` (SHA-256 `c52d859987ac7f65f6e18dd49a7287d10f93011d3ed6b0696bfdafb775b2a810`). Effective config confirms vayu, WALT, SchedTune, KGSL, ZRAM, schedutil, ThinLTO and performance optimization. This config-generation check does not require or demonstrate a kernel compile.

No compiler, LLD, LLVM utilities, bison/flex, AArch64/ARM32 cross toolchains, dtc, ccache, libelf-dev, or ncurses-dev are installed. OpenSSL/zlib headers and host make/Python/Perl/Git/bc are present. No package installation was attempted because the sandbox prohibits network sockets and system package mutations. The preexisting `build.sh` was not run: it deletes `out/` and deletes ZIPs from `/root/AnyKernel3`, and hard-codes root-owned toolchain paths. No permitted AnyKernel3 packaging tree exists in the checkout, so a flashable ZIP cannot be created safely or truthfully.

**Build result:** not started; no compiler exit status, image, release, resource measurement or ZIP exists. No Actions workflow was dispatched. See `VPS_BUILD_R614150_REPORT.md` for the full blocker evidence and remediation.
