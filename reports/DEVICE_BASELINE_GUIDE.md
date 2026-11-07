# Rooted Poco X3 Pro baseline collection guide

This procedure collects a bounded, read-only snapshot from a rooted Android device. It does not change governors, frequency limits, CPU online state, thermal settings, charging settings, or other kernel controls. No physical device has been tested from this workstation; confirm the target reports `vayu` and review node statuses rather than assuming a path exists.

## Before collection

1. Use the intended baseline kernel and userspace. Record which kernel image/source SHA is running and do not compare snapshots from unlike configurations as if they were equivalent.
2. Follow the controlled conditions in [RUNTIME_BASELINE.md](RUNTIME_BASELINE.md): battery band, ambient temperature, screen/refresh settings, network state, workload, cooldown, and run repetition.
3. Enable USB debugging and approve the host. In Termux, install/use the `termux-tools` package only if `getprop`, `uname`, or shell tools are needed locally; the collector uses Android `/system/bin/sh` and system utilities. Confirm root authorization in the device's root manager.
4. On the VPS checkout, make the script available at `scripts/xen-baseline/collect-device.sh`. On the host, confirm `sh -n scripts/xen-baseline/collect-device.sh` succeeds.

## Recommended ADB procedure

Run these commands on the workstation connected to the phone. Replace `<serial>` only if more than one ADB device is connected. The output directory name must be new; the collector refuses to overwrite an existing directory.

```sh
SERIAL='device-serial-from-adb-devices'
adb devices -l
adb -s "$SERIAL" shell getprop ro.product.device
adb -s "$SERIAL" shell uname -r
adb -s "$SERIAL" push scripts/xen-baseline/collect-device.sh /data/local/tmp/xen-collect-device.sh
adb -s "$SERIAL" shell su -c 'sh /data/local/tmp/xen-collect-device.sh /sdcard/xen-vayu-baseline-20261106-120000'
```

The last argument is an example unique folder name; use the actual UTC date/time. Check the command output says `Read-only collection complete`. If root approval is denied, stop and authorize the command through the root manager; do not try to work around Android permissions by changing SELinux or kernel settings.

Verify identity and result listing:

```sh
adb -s "$SERIAL" shell getprop ro.product.device
adb -s "$SERIAL" shell 'ls -la /sdcard/xen-vayu-baseline-20261106-120000'
adb -s "$SERIAL" shell 'cat /sdcard/xen-vayu-baseline-20261106-120000/metadata.txt'
adb -s "$SERIAL" shell 'head -n 12 /sdcard/xen-vayu-baseline-20261106-120000/manifest.tsv'
```

Expected codename is `vayu`. A different value means the collection is not the target device and should be labeled accordingly, not silently treated as Poco X3 Pro data.

## Termux alternative

Copy the script into shared storage from the workstation, then invoke it through `su` from Termux. Shared storage may be mounted `noexec`, so invoke the script with `sh` rather than executing it directly.

```sh
adb -s "$SERIAL" push scripts/xen-baseline/collect-device.sh /sdcard/Download/xen-collect-device.sh
```

In Termux:

```sh
su -c 'sh /sdcard/Download/xen-collect-device.sh /sdcard/xen-vayu-baseline-20261106-120000'
```

Use a unique path. The collector requires root for physical collection and reports errors if the output location cannot be created. Do not use the mock-root environment variable on a phone.

## Output and completeness

The collector creates one directory containing:

- `metadata.txt`: timestamp, product/build properties, Android version, kernel release/version, UID, and SELinux mode where readable.
- `manifest.tsv`: one row per requested interface, with `collected`, `unavailable`, `permission_denied`, or `read_error` status, source path, output file, and detail.
- One file per captured procfs/sysfs/debugfs node, named from its path. A `dmesg.txt` snapshot is included when permitted.

Read `metadata.txt` and the full manifest before interpreting values. A missing node is not zero and does not establish that hardware or a feature is absent. Permission-denied means the node was discovered but not readable in that context. Unavailable means the named path/glob did not resolve. Read error means the path existed but the read failed for another reported reason. Keep the original files even if you later create a redacted review copy.

Check for at least these groups in the manifest: CPU online/possible/present/isolated/nohz_full, per-CPU cpufreq and policy interfaces, cpuidle states, scheduler sysctls, schedtune scalar controls under known Android cgroup mount points, core_ctl, KGSL/devfreq, thermal zones/cooling devices, power supplies, meminfo/vmstat/swaps/ZRAM/pressure, block-device queue policies/statistics and /proc/diskstats, suspend/wakeup diagnostics, and dmesg. Some vendor interfaces may be absent. In particular, do not assume a KGSL, WALT, schedtune, core_ctl, debugfs, PSI, or block queue path exists until this collection reports it.

The collector produces point-in-time snapshots; it does not trace wakeups or produce high-rate frequency timelines. Capture separate snapshots immediately before and after a workload to calculate cumulative counter deltas where counters exist. Keep each run in its own folder. Storage queue attributes are configuration snapshots; /proc/diskstats and per-device stat files are cumulative counters, not latency histograms.

## Transfer and preservation

Pull to a private host directory without flattening or renaming individual files:

```sh
mkdir -p "$HOME/xen-baselines"
adb -s "$SERIAL" pull /sdcard/xen-vayu-baseline-20261106-120000 "$HOME/xen-baselines/"
tar -C "$HOME/xen-baselines" -czf "$HOME/xen-baselines/xen-vayu-baseline-20261106-120000.tar.gz" xen-vayu-baseline-20261106-120000
sha256sum "$HOME/xen-baselines/xen-vayu-baseline-20261106-120000.tar.gz" > "$HOME/xen-baselines/xen-vayu-baseline-20261106-120000.tar.gz.sha256"
```

Transfer the archive and checksum over authenticated SSH to a restricted VPS directory. Verify using the checksum file on the VPS (`sha256sum -c ...`) before unpacking. Preserve the original archive, checksum, directory structure, metadata, manifest, and raw node files; perform analysis on a copy. Avoid public paste sites and public issue attachments.

## Privacy and log handling

The collector deliberately avoids app data, `/data`, full bugreports, and logcat. Its single `dmesg` capture can still contain device identifiers, network names, process/service names, or other operational details; build fingerprints and ROM properties identify the device configuration. Store the original archive with limited access. Review a copy locally before sharing; redact that copy only, document the redactions, and never replace raw evidence with an edited version.

The script performs one bounded pass over named interfaces and captures dmesg once. It does not poll repeatedly or recursively walk debugfs. Do not add a fast polling loop for routine baselines. If a later latency study needs tracing, define a separate short, targeted trace window and compare with an untraced run because instrumentation can add overhead.

## Repeatable baseline blocks

Use [RUNTIME_BASELINE.md](RUNTIME_BASELINE.md) for the full protocol. In brief, use the same device, ROM, kernel/config, app versions, battery state band, charger state, ambient temperature, display brightness/refresh, network conditions, and workload. Reboot, idle/cool to a repeatable starting temperature, capture a pre-run snapshot, perform a documented workload, and capture a post-run snapshot. Repeat at least five times, retain every run, and report the median plus spread. Record changes and anomalies; do not alter kernel controls to make a run comparable.

No device baseline or runtime result is included in this guide. Physical collection remains pending.
