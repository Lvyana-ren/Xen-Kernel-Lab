# Security and stability review

## Scope reviewed

The experiment branch adds build workflow metadata and exact patches: one include fix in `hyp_core_ctl.c`, one exact `EXTRAVERSION` transform, and a bounded read-only baseline collector. The collector writes only to a selected output directory, refuses to overwrite an existing directory, reports missing/permission/read errors, and reads a finite list of procfs/sysfs/debugfs paths plus one dmesg snapshot. Recent collector additions read CPU isolation masks, named schedtune scalar files and block-device queue/counter files; no task lists are read.

## Security and stability observations

- Exact patch context mismatch stops the build; source SHA and patch hashes/application list are captured.
- Build dependency sources remain mutable: Ubuntu 22.04 runner, apt package resolution, Clang branch 15.0 and Actions major tags. Per-run versions are recorded, but not fully hermetic.
- Collector output may contain device fingerprint, kernel logs, power state, group names and storage device identifiers. Protect archives and redact only a copy before sharing.
- No write to CPU/GPU/thermal/charging controls is added by collector. No thermal trips, voltage/frequency ranges or battery safety controls are modified.
- `CONFIG_THERMAL_WRITABLE_TRIPS` exists in the baseline; it is not used by this work.
- Patch header and release changes need build/boot validation. No kernel image or device exists to inspect for warnings, boot behavior or regressions.

## Status

Static review only. No build, boot, fuzzing, static analyzer, lockdep, KASAN, suspend test or security scan was run. There is no new runtime security/stability claim. Promotion is blocked on successful CI and physical-device validation.
