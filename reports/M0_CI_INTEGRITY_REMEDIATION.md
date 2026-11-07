# M0 CI integrity remediation

**Branch reconciliation:** this report was originally prepared before CI publication. At the current mission start, HEAD `1d7baee8d8363b1a1369bd1b3e654e30d5d5cc87` is published on `origin/experiment/m0-m1-reproducible-baseline` and includes the workflow, both patch files, and collector. This does not mean Actions or device validation ran; GitHub reports zero workflow runs on the experiment branch.

## Summary

The previous pre-CI review identified conditional edits to hyp_core_ctl.c, a ZRAM default rewrite, and release suffix normalization. The workflow now represents required source transformations as exact-context patch files, removes the ZRAM source rewrite, and captures source, patch, configuration, release, build, and artifact provenance.

Recommendation: READY FOR MANUAL CI after the operator publishes the experiment branch with the workflow and both files under ci-patches/ together.

No Actions run, full kernel build, physical-device collection, commit, push, or flash was performed. No CPU/GPU/thermal/charging tuning was changed.

## Workflow source/configuration mutation audit

| Operation | Original value → resulting value | Reason and compiled/runtime effect | Applicability | Deterministic/idempotent |
|---|---|---|---|---|
| ci-patches/0001-hyp-core-ctl-include-cpu-header.diff | Adds #include <linux/cpu.h> after #include <linux/init.h> in drivers/soc/qcom/hyp_core_ctl.c. The driver references cpu_subsys; include/linux/cpu.h declares extern struct bus_type cpu_subsys. | Makes the declaration visible to this translation unit and addresses the existing compile failure. It affects compilation/source contents, not runtime algorithm or tuning. | Every workflow build checks source reference and header declaration. Patch applies only where exact nearby source context matches; mismatch fails. Source-context-specific, not branch-name-specific. | Fixed patch bytes/context. The workflow applies once or records already-applied only when reverse-check confirms the exact patch. Repeated application has stable output. |
| Removed ZRAM mutation; added assertion | Old workflow rewrote default_compressor to lz4 if different. Current tracked implementation already has static const char *default_compressor = "lz4". vayu_defconfig has CONFIG_ZRAM=y; there is no Kconfig/.config compressor selection symbol in this tree. | Previous rewrite could alter compiled runtime behavior. New workflow only asserts the intended LZ4 baseline and stops if source differs. No C, Kconfig, defconfig, or generated config edit is made for compressor selection. | Assertion runs every build and depends on the source value. | Read-only, deterministic, no source mutation. |
| ci-patches/0002-xen-release-extraversion.diff | Exact Makefile value EXTRAVERSION = -openela → EXTRAVERSION =. | Removes only the known packaging suffix to meet Xen release naming. Affects kernel release/module naming metadata, not CPU/GPU/thermal/charging behavior. | Both Xen and KSUN workflow variants; exact patch context required. Unexpected source value fails closed. | Fixed one-line patch; the apply/reverse-check logic is repeatable. No arbitrary suffix stripping. |
| scripts/config plus olddefconfig | Generated out/.config receives requested LOCALVERSION, disables LOCALVERSION_AUTO, enables LTO/LTO_CLANG/THINLTO/performance optimization, disables LTO_NONE/size optimization, then Kconfig resolves dependencies. | Generated build configuration only; no tracked source or runtime tunable writes. Preserves existing compiler and ThinLTO strategy. | Every workflow build; effective config depends on selected source/Kconfig/toolchain and is hard-checked after olddefconfig. | Repeatable for identical source, toolchain, inputs, and Kconfig. |
| Kernel build and artifact collection | Generates out/, logs, metadata and artifacts. | Build outputs only; no additional source transformation. | Outputs depend on the build and reached steps. | Source, configuration, tool and output provenance is recorded; hashes are generated for collected artifact files. |

The workflow no longer uses Python to write hyp_core_ctl.c, zram_drv.c, or Makefile. The only tracked kernel source transformations are the two listed patch files. The configuration operations modify generated out/.config.

## hyp_core_ctl.c patch details

The former conditional edit was triggered when cpu_subsys appeared in drivers/soc/qcom/hyp_core_ctl.c, its declaration appeared in include/linux/cpu.h, and the include itself was absent. The old code failed if it could not find the declaration. The current checked-in driver references cpu_subsys in its sysfs group creation, and include/linux/cpu.h contains the extern declaration. The driver currently lacks the include.

The workflow now validates the source reference and declaration, then uses git apply --check on the version-controlled patch. A mismatch fails before configuration or compilation. The patch adds exactly one include at a context anchored around the initial include block. It applies to any selected source ref with the expected code context, not just a branch with a particular name. Patch file bytes, SHA256, application status, original source SHA, and post-patch diff are captured.

## ZRAM default compressor

At the reviewed source revision, drivers/block/zram/zram_drv.c declares LZ4 as the implementation default. vayu_defconfig enables ZRAM with CONFIG_ZRAM=y and disables optional ZRAM dedup/writeback, but has no compressor-selection symbol. drivers/block/zram/Kconfig likewise does not define a compressor selector.

Previously the workflow edited drivers/block/zram/zram_drv.c when its literal default was not LZ4. This could change runtime behavior and was an implicit source mutation. That write is removed. The workflow now confirms the source contains exactly an identifiable default value of lz4; any other or unrecognized source value stops the build without editing it. Runtime implementation remains unchanged.

## EXTRAVERSION and release validation

The checked-in Makefile has exactly EXTRAVERSION = -openela. The release patch encodes that complete expected context and transforms only its value to empty. Patch application fails for any other value or context. No regular expression strips arbitrary suffixes.

The workflow validates the flavor choice and positive generation, sets Xen LOCALVERSION to -Xen+N or KSUN to -Xen-KSUN+N, and keeps LOCALVERSION_AUTO disabled. After kernelrelease it checks the entire value against the selected Xen pattern and against 4.14.357 concatenated with the requested LOCALVERSION. The compiled build then compares the stored validated value with out/include/config/kernel.release.

With generated effective local-version configurations, make kernelrelease returned 4.14.357-Xen+3 and 4.14.357-Xen-KSUN+3. This validates naming logic, not a full Clang build.

## Provenance and artifact changes

Before patching, the workflow records the checked-out source commit as original-source-sha.txt. Each patch gets a row in applied-patches.txt with status, path and SHA256. Exact patch files are copied into artifacts/ci-patches and independently hashed. post-patch-source.diff records the tracked source diff relative to the original source SHA. Final out/.config, kernel.release, config/release validation, verbose build log, compiler/linker versions, runner/package metadata, ccache stats, image checksum/size, and an artifact checksum manifest are collected. The manifest hashes every artifact file present at creation, excluding the manifest itself. Retention is 30 days.

Patch-file hashes in this review workspace:

- ci-patches/0001-hyp-core-ctl-include-cpu-header.diff: b5e536ecba018da34eb43daa8d76f164e0152c802457be1d8a560935d2daa79c
- ci-patches/0002-xen-release-extraversion.diff: 1b2ab725950a6f760ca740ae3b3c7e2a003f8e8c505e16d4dc0d63a94052204c

The Clang ref remains mutable branch 15.0; each run records its resolved commit and content-tree checksum. ubuntu-22.04, apt repositories, and Actions @v4 references also remain mutable. Runner metadata, installed package versions, and declared dependency references are recorded, but immutable Actions SHAs and a verified current upstream Clang SHA are not available here.

## Validation evidence

- Workflow YAML parsed; dispatch source_ref binding, choice/default values, source checkout binding, artifact path, and 30-day retention assertions passed.
- Every embedded workflow Bash block passed bash -n.
- Both patch files passed git apply --check against the current experiment source.
- An isolated temporary Git copy applied both patches; the second application recognized the exact postimage, and its source diff matched the first-pass diff byte-for-byte.
- Release patch plus effective config generation produced and validated Xen+3 and Xen-KSUN+3 release values.
- Source selection checks were statically reviewed: requested branch/SHA is resolved and compared to checked-out HEAD; unknown branch fails closed. No Actions checkout was performed.
- ThinLTO Kconfig dependencies, workflow enable/validation logic after olddefconfig, and actual-build -flto=thin/LLD guards were inspected. This environment has no clang or ld.lld, so a fresh Clang-enabled olddefconfig or compiler log could not be produced. Hosted CI must confirm effective config and actual compiler invocation.
- Collector sh -n and git diff --check passed. Static review found collector writes only to the chosen collection output directory, not device control nodes.
- No full build, workflow dispatch, or physical-device collection was performed.

## Changed files

Kernel repository:

- Modified: .github/workflows/build-kernel.yml
- Added: ci-patches/0001-hyp-core-ctl-include-cpu-header.diff
- Added: ci-patches/0002-xen-release-extraversion.diff
- M1 collector: scripts/xen-baseline/collect-device.sh

No tracked C source, Kconfig, defconfig, or runtime tuning file was modified locally.

Workspace-level reports updated outside the nested Xen-Kernel Git repository:

- reports/M0_CI_INTEGRITY_REMEDIATION.md
- reports/FINAL_PRE_CI_REVIEW.md
- reports/M0_HARDENING_REVIEW.md
- reports/BUILD_BASELINE.md

At report generation, tracked nested repository diff summary is .github/workflows/build-kernel.yml with 223 insertions and 68 deletions. git diff --stat omits the two new untracked patch files and the existing untracked collector. No commit or push was made.

## Remaining limitations and readiness

- The operator must publish the workflow and both patch files together before running CI. An older branch revision lacking the patch files will fail.
- No hosted Actions artifacts or complete build evidence exist.
- The Clang source branch, hosted runner label, apt repositories, and Actions major tags remain mutable; provenance narrows but does not eliminate that source of nondeterminism.
- Rooted vayu collection, runtime behavior, benchmarks, and thermal/energy results remain pending.

READY FOR MANUAL CI after publication of the full experiment branch state. This does not claim build or runtime validation.
