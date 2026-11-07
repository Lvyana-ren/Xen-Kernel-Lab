# M0/M1 hardening review

**Status reconciliation (2026-11-07):** the branch is now published at `1d7baee8d8363b1a1369bd1b3e654e30d5d5cc87`, tracking origin, and includes the workflow, two patches and collector. The historical statements below that refer to untracked files describe their original review snapshot. A read-only GitHub Actions query for this branch returned zero runs; hosted build and device acceptance remain pending.

## 1. Summary

M0 workflow provenance, source selection, release validation and evidence capture have been hardened on the experiment branch. M1 collector and protocol are improved and locally checked with mock nodes. The workflow has not been dispatched, no full build was run, and no physical device data exists. Therefore source-level changes are reviewable, but CI artifact acceptance and runtime baseline acceptance remain pending.

## 2. Changed files

- `Xen-Kernel/.github/workflows/build-kernel.yml` — explicit source/release inputs, exact checkout validation, reproducibility metadata, ThinLTO build evidence, release validation and complete tracked/untracked mutation capture.
- `Xen-Kernel/ci-patches/0001-hyp-core-ctl-include-cpu-header.diff` — exact-context compile fix for the existing cpu_subsys reference.
- `Xen-Kernel/ci-patches/0002-xen-release-extraversion.diff` — exact-context release suffix normalization.
- `Xen-Kernel/scripts/xen-baseline/collect-device.sh` — read-only bounded device collection with structured output and status manifest; mock-root mode for host validation.
- `reports/BUILD_BASELINE.md` — current build/runtime collection specification.
- `reports/RUNTIME_BASELINE.md` — controlled measurement conditions and clearly empty results section.
- `reports/M0_M1_FINDINGS.md` — updated summary.
- `reports/M0_HARDENING_REVIEW.md` — this review.
- `reports/CPU_RESEARCH.md` — M2 source research.
- `reports/DEVICE_BASELINE_GUIDE.md` — rooted ADB/Termux collection, transfer, privacy and completeness procedure.
- `reports/CPU_BASELINE_CHECKLIST.md` — collector snapshot versus trace measurement checklist.
- `reports/M0_CI_INTEGRITY_REMEDIATION.md` — source mutation audit and remediation evidence.
- `reports/FINAL_PRE_CI_REVIEW.md` — refreshed readiness assessment.

The initial audit was reviewed and retained as historical scope evidence. It was not rewritten to hide what was unknown at its earlier read-only stage.

## 3. M0 findings

Workflow source selection previously hardcoded branch `16`. Dispatch now accepts `source_ref`, default `16`; it supports branch names and commit SHAs and fails if the resolved checkout SHA differs or a branch was not fetched. Requested kernel source identity is recorded separately from the workflow event ref/SHA. `fetch-depth: 0` provides source refs for validation.

ThinLTO is implemented by `CONFIG_THINLTO` in `arch/Kconfig`, depending on `LTO_CLANG` and architecture support. `CONFIG_LTO_CLANG_THIN` in vayu defconfig is not the effective option and was not substituted or removed. Workflow continues to enable/check `LTO`, `LTO_CLANG`, `THINLTO`, and performance optimization after `olddefconfig`. Build runs verbose and will fail if the log does not contain `-flto=thin` and `ld.lld` evidence. No full build was run, so actual compiler command evidence is pending a manual workflow run.

Build artifacts capture requested source ref and resolved SHA, workflow trigger ref/SHA, original checked-out source SHA, source-validation result, Clang/LLD and cross GCC/binutils/Make versions, toolchain Git commit and sorted-tree SHA256, runner OS/image data, source-derived Kbuild timestamp, workflow start/artifact times, final `.config`, config validation, release validation and generated `kernel.release`, image SHA256/size, verbose build log, ccache stats, worktree state, exact applied patch files/hashes/list, post-patch source diff, and archive/list of untracked files. A checksum manifest covers collected artifacts. Retention is 30 days. `mutable-dependencies.txt` identifies the hosted runner label, apt repositories and per-run installed Debian package versions, declared Actions major tags, and mutable Clang branch.

The Clang repository currently resolves `15.0` at build time and records the actual commit and content-tree SHA256. Its exact current branch commit could not be independently queried from this VPS because GitLab DNS/network access was unavailable. No fixed SHA is asserted or introduced. A SHA checkout can preserve existing behavior only after confirming it is the current `15.0` tip and that the same cloned tree produces the same Clang/LLD version and content hash; until that evidence is available, this remains a mutable dependency and an M0 limitation. The repository URL, branch, compiler release, and ThinLTO choices are unchanged.

The release naming contract is `4.14.357-Xen+N` or `4.14.357-Xen-KSUN+N`. Workflow inputs make flavor and positive generation explicit. `LOCALVERSION_AUTO` remains disabled to avoid Git-derived suffixes. The prepared patch file `ci-patches/0002-xen-release-extraversion.diff` changes only the exact observed source line `EXTRAVERSION = -openela` to an empty `EXTRAVERSION =`; patch context mismatch fails the workflow. It validates the generated release against the requested flavor/generation and compares it with `include/config/kernel.release`. This preserves the specified product release label without stripping arbitrary suffixes. The exact generated CI release remains pending.

The `hyp_core_ctl.c` include edit is an exact-context patch in `ci-patches/0001-hyp-core-ctl-include-cpu-header.diff`. The workflow verifies that the source uses `cpu_subsys` and `include/linux/cpu.h` declares it, then applies or recognizes the exact patch; changed context fails closed. ZRAM source already has `default_compressor = "lz4"` at the reviewed source revision. The workflow no longer writes `drivers/block/zram/zram_drv.c`; it asserts that the intended baseline is still present. `CONFIG_ZRAM=y` is set in vayu defconfig, but compressor selection is not a Kconfig/.config symbol in this tree.

## 4. M1 findings

The collector is read-only with respect to kernel/system interfaces. All writes are directed to its selected output directory. It does not write sysfs, procfs, debugfs or tuning controls; it does not change CPU online state, governor, frequencies, thermal or charging settings. Collection is bounded to named nodes/globs and one dmesg snapshot; it no longer recursively copies whole debugfs trees.

`metadata.txt` records collection time, device/ROM/build properties, kernel version, UID and SELinux mode where available. `manifest.tsv` is structured with four columns: status, source path, output file and detail. Status distinguishes `collected`, `unavailable`, `permission_denied`, and `read_error`; missing values are not replaced with zero. Captured data includes CPU online/frequency/idle/core_ctl, scheduler sysctls, KGSL/devfreq, thermal/cooling, power supplies, memory/ZRAM, suspend/wakeup diagnostics, and dmesg where accessible. Rooted-device permission behavior and exact vayu node presence remain unverified.

`RUNTIME_BASELINE.md` separates protocol from results and defines battery/ambient/display/network/workload/cooldown controls, five repetitions, randomized ordering, median/spread/tail reporting, temperature monitoring, logging, and suspend/resume procedure. Results remain empty pending physical collection.

## 5. ThinLTO verification evidence

- `arch/Kconfig`: `THINLTO` depends on `LTO_CLANG` and `ARCH_SUPPORTS_THINLTO`; `LTO_CLANG` selects `LTO`.
- `arch/arm64/configs/vayu_defconfig`: `CONFIG_LTO=y`, `CONFIG_LTO_CLANG=y`, stale `CONFIG_LTO_CLANG_THIN=y`, performance optimization selected.
- Workflow: explicit `scripts/config --enable LTO --enable LTO_CLANG --enable THINLTO`; `olddefconfig`; hard checks in output `.config`.
- `Makefile`: when `CONFIG_LTO_CLANG` and `CONFIG_THINLTO` are set, it adds `-flto=thin` and `--thinlto-cache-dir`.
- Local verification: configured vayu defconfig and applied workflow config overrides; immediate `olddefconfig` output had `CONFIG_LTO=y`, `CONFIG_LTO_CLANG=y`, `CONFIG_THINLTO=y`, and `CONFIG_CC_OPTIMIZE_FOR_PERFORMANCE=y`. A later local `kernelrelease` invocation without Clang disabled Clang options, so local config output does not substitute for workflow execution with the intended toolchain. Separately, `make kernelrelease` in `/tmp` with command-line `EXTRAVERSION=` produced `4.14.357-Xen+3`; setting only the temporary config's `LOCALVERSION` to `-Xen-KSUN+3` produced `4.14.357-Xen-KSUN+3`. This validates generated naming logic locally, not the full workflow's post-mutation artifact.

## 6. Source ref verification

The current workflow default remains branch `16`; an operator can select the experiment branch name or commit SHA when manually dispatching. Checkout action receives the input directly. Validation resolves branch refs from checkout's local/remote refs or resolves a commit SHA, then compares it against `HEAD`; failed/missing resolution exits before building and does not fall back to `16`. The workflow-trigger `GITHUB_REF`/`GITHUB_SHA` are separately recorded. No workflow dispatch was performed.

## 7. Kernel release validation

The source `Makefile` currently says `EXTRAVERSION = -openela`. Workflow clearing is guarded by an exact match, and final generated release must satisfy the selected Xen or Xen-KSUN pattern with the requested generation. `LOCALVERSION` contains the requested label/generation and `LOCALVERSION_AUTO` is disabled. This is a justified build-local normalization to maintain the explicitly required release naming contract. Build-time diff artifacts preserve the Makefile mutation. No final CI release value has been observed.

## 8. Collector safety assessment

Static review found output-file creation and reads of listed pseudo-files; no writes to kernel control nodes. The test-only `XEN_BASELINE_TEST_ROOT` redirects input paths to mock nodes and bypasses root requirement only in that explicit test mode. Output files may include device identity, package/build fingerprint, kernel logs and operational states; store/share collected archives according to project policy. Device output path should be selected with adequate free storage.

## 9. Validation performed

- `sh -n scripts/xen-baseline/collect-device.sh` passed.
- YAML parsed with PyYAML; all 10 embedded Bash workflow blocks passed `bash -n`. Dispatch defaults/options and checkout `ref` binding were asserted.
- Source-ref logic accepted the selected experiment branch and exact current SHA, and failed closed for an absent branch. Release-pattern checks accepted both naming conventions and rejected the old `-openela` suffix and generation zero.
- Mock-node execution verified TSV column count, collection of a present CPU-online node, explicit `unavailable` and `permission_denied` statuses, metadata header, and refusal to overwrite an existing output directory.
- Both exact-context build patch files passed `git apply --check`; an isolated temporary Git copy verified that applying the patches a second time produced an unchanged diff.
- Patched release Makefile plus effective local-version configurations produced and validated Xen+3 and Xen-KSUN+3 release names.
- This host has no Clang/LLD, so no fresh Clang-enabled `olddefconfig` result or actual build log was produced during this remediation. Workflow hard checks and hosted CI remain the evidence gate.
- Static collector review found no writes to `/sys`, `/proc`, or debugfs; writes target the new output directory only.
- Earlier local `vayu_defconfig`, workflow config overrides and `olddefconfig` verified effective ThinLTO/performance selections before later toolchain-aware config re-evaluation.
- Workflow YAML/input/build logic and Kconfig/source paths were reviewed. `git diff --check` passed after remediation.

## 10. Validation not performed

- No Actions dispatch, Actions artifact review, toolchain download/checksum run, full kernel build, build reproducibility comparison or image flash.
- No collector run on Android or physical Poco X3 Pro; SELinux and sysfs behavior not validated.
- No boot, suspend/resume, CPU wakeup/frequency latency, performance/energy/temperature measurement or benchmark.
- The actual GitHub Actions source checkout/artifact pipeline was not run; local validation of its ref logic does not test Actions checkout behavior.

## 11. Remaining blockers

1. Authorized manual Actions run required to confirm source checkout behavior, exact runner metadata, effective Clang-enabled `.config`, actual `-flto=thin`/LLD log evidence, image/release consistency and all artifact paths.
2. Rooted physical vayu and stock baseline image required to gather actual runtime observations and identify live schedtune/cpufreq/core_ctl/LPM state.
3. The toolchain source is still a mutable upstream branch. CI records its resolved commit and content-tree SHA256 per run, but the current upstream branch SHA could not be verified from this network-restricted environment; no fixed pin or immutable action commit has been established.

## 12. Risks

- `ubuntu-22.04` is a mutable runner image label and apt installs are not version locked; resolved Debian package versions are now included in `mutable-dependencies.txt` for each run.
- Full-depth fetch adds history/network cost; it is used to resolve a requested branch and commit reliably.
- Verbose build logs can be large; artifact retention is 30 days.
- Artifact capture for untracked files uses a tar archive; paths are listed separately for inspection.
- The collector's interfaces vary across vendor Android releases. Missing nodes must be manually supplemented rather than interpreted as unsupported hardware or zero state.
- Release normalization intentionally fails if a requested source has an unexpected `EXTRAVERSION`; that is a safe stop requiring source review.

## 13. Recommended next actions

1. Technical lead reviews this report, workflow changes and CPU research before any runtime tuning.
2. An authorized operator manually runs CI with `source_ref=experiment/m0-m1-reproducible-baseline` and reviews all provenance/config/release/image artifacts.
3. Collect the physical baseline with the matching kernel/DT/userspace and reviewed collector output.
4. Use CPU research methodology to identify a measured bottleneck; propose one reversible CPU experiment for separate approval.

## 14. Final acceptance checklist

- [x] Explicit source ref input is checked out and validated against the actual commit; failed refs stop before build.
- [x] Workflow trigger ref/SHA and kernel source ref/SHA are captured separately.
- [x] `olddefconfig` output checks effective `LTO`, `LTO_CLANG`, `THINLTO`, and performance optimization; verbose build checks `-flto=thin` and LLD invocation.
- [x] Requested release flavor/generation is checked against both naming pattern and generated `include/config/kernel.release`.
- [x] Artifact collection retains config, logs, provenance, diffs/untracked source mutations, image hash/size, ccache stats, runner/tool versions, and mutable dependency declarations/installed package versions; retention is 30 days.
- [x] Source transformations are version-controlled exact-context patches, with source SHA, patch SHA256, application status/list, patch copies, post-patch source diff and artifact checksums captured.
- [x] ZRAM runtime source is not edited by the workflow; the existing LZ4 default is asserted and mismatch fails closed.
- [x] EXTRAVERSION normalization is limited to the exact `-openela` source value and is represented by a reviewed patch; release is checked against flavor and generation.
- [x] Workflow validation confirms the requested `source_ref` is passed to checkout, the dispatch default remains `16`, the artifact path is `artifacts/`, and the configured expiry is 30 days.
- [x] Collector is read-only on device interfaces and has structured missing/permission/read-error reporting; host mock validation was performed.
- [ ] Manual Actions execution and artifact review remain pending; M0 CI acceptance is not complete until those artifacts are inspected.
- [ ] Current Clang branch SHA and equivalent immutable checkout have not been verified; toolchain pinning remains open. Actions use mutable `@v4` tags whose resolved action commits are also not recorded in-job.
- [ ] Rooted physical vayu collection and runtime validation remain pending.
