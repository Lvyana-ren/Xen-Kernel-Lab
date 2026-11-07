# Matched toolchain build comparison

## Status

**Neither build ran.** No kernel image, `.config` for a toolchain build, image checksum, build log, duration, peak RSS, or ZIP exists. The VPS cannot resolve `android.googlesource.com`, has no Clang/LLD or required cross compiler binaries, and the working tree changes remain uncommitted. No Actions dispatch or publication was performed.

| Input/result | A: baseline | B: experimental | Comparison status |
|---|---|---|---|
| Source branch / HEAD | `experiment/m0-m1-reproducible-baseline`, `1d7baee8d8363b1a1369bd1b3e654e30d5d5cc87` plus dirty worktree | Must use identical full source tree/diff as A | Not built; current uncommitted source state is not represented by HEAD alone |
| Compiler | Existing Clang r547379 GitLab source, branch `15.0` | Official AOSP clang-r614150, LLVM 23.0.1, pinned source commit `16fae8ef5b856b1d3e02a55274e4327c5842bb34` | r547379 not installed locally; r614150 archive not acquired |
| CPU experiment | `baseline` | `baseline` | Intended matched selection |
| Memory experiment | `baseline` | `baseline` | Intended matched selection |
| Release | Xen flavor, generation 3 | Xen flavor, generation 3 | Intended `4.14.357-Xen+3`; not generated |
| Config | vayu defconfig + existing ThinLTO/performance settings | Same exact effective `.config` | No build `.config`; only independent `olddefconfig` experiment checks exist |
| Build/image | None | None | No result or checksums |

## Workflow selection

The new workflow input `toolchain` defaults to `clang-r547379` and allows `clang-r614150`. Run two separate manual Actions invocations with the exact same full source SHA, `release_flavor=xen`, `release_generation=3`, `cpu_experiment=baseline`, and `memory_experiment=baseline`; change only `toolchain`. The current user authorization forbids dispatch and the updated workflow is not published, so these runs remain operator actions.

For direct VPS builds after toolchain acquisition, use isolated output directories and conservative `-j2`. Build both from the same reviewed working-tree state, including the same exact M0 patch application, and record a source diff digest if the tree is dirty. Compare final `.config` byte-for-byte after normalizing only documented toolchain-generated fields (ideally none), release, compiler/linker identity, build log, elapsed build time, peak RSS, image size and SHA-256. Do not compare images as reproducible byte-identical unless build metadata is normalized and that property is specifically tested.

## Required artifact set per successful build

- Kernel `Image` and any actual packaged/compressed output produced by the build.
- `kernel-release.txt`, final `kernel.config`, source identity and dirty/source patch diff digest.
- Selected toolchain ID, pinned source, archive SHA-256, Clang/LLD version output, LLVM utility resolution, cross compiler versions.
- Build log, config validation, ThinLTO command evidence, duration/resource record, image size and SHA-256.
- `artifact-checksums.sha256`, a short build report, and a ZIP bundle.

The workflow now creates a toolchain/flavor/generation-named ZIP only when a non-empty `Image` exists. It includes image, release, config, source/toolchain provenance, build log/report, checksums and optional resource log, then writes a ZIP SHA-256 sidecar. No ZIP or artifact directory is listed locally because no build completed. No Termux download is available until a real artifact exists and is placed on a reachable VPS or uploaded through an authorized artifact service.
