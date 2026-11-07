#!/system/bin/sh
# Read-only, bounded snapshot collector. Run as root on the target Android device.
set -u

OUT=${1:-"/sdcard/xen-baseline-$(date +%Y%m%d-%H%M%S)"}
if [ -e "$OUT" ]; then
    echo "Output path already exists; choose a new directory to preserve prior data: $OUT" >&2
    exit 1
fi
mkdir -p "$(dirname "$OUT")" 2>/dev/null && mkdir "$OUT" 2>/dev/null || {
    echo "Cannot create new output directory: $OUT" >&2
    exit 1
}
TEST_ROOT=${XEN_BASELINE_TEST_ROOT:-}
if [ -z "$TEST_ROOT" ] && [ "$(id -u 2>/dev/null)" != 0 ]; then
    echo "Run as root (for example: adb shell su -c '/data/local/tmp/collect-device.sh /sdcard/xen-baseline')" >&2
    exit 1
fi

META="$OUT/metadata.txt"
MANIFEST="$OUT/manifest.tsv"
printf 'key\tvalue\n' > "$META"
printf 'status\tpath\tfile\tdetail\n' > "$MANIFEST"

meta() {
    key=$1
    shift
    value=$("$@" 2>/dev/null)
    [ -n "$value" ] || value='unavailable'
    value=$(printf '%s' "$value" | tr '\t\r\n' '   ')
    printf '%s\t%s\n' "$key" "$value" >> "$META"
}

meta collected_at date -Iseconds
meta device_model getprop ro.product.model
meta device_codename getprop ro.product.device
meta build_fingerprint getprop ro.build.fingerprint
meta rom_version getprop ro.build.display.id
meta android_release getprop ro.build.version.release
meta build_type getprop ro.build.type
meta cpu_abi getprop ro.product.cpu.abi
meta boot_mode getprop ro.bootmode
meta boot_slot getprop ro.boot.slot_suffix
meta kernel_release uname -r
meta kernel_version uname -v
meta collection_uid id
meta selinux_mode getenforce
meta shell getprop ro.boot.shell

read_node() {
    src=$1
    dest=$2
    logical=${3:-$src}
    if [ ! -e "$src" ]; then
        printf 'unavailable\t%s\t\tpath does not exist\n' "$logical" >> "$MANIFEST"
        return
    fi
    if [ ! -r "$src" ]; then
        printf 'permission_denied\t%s\t\tread permission check failed\n' "$logical" >> "$MANIFEST"
        return
    fi
    if cat "$src" > "$dest" 2> "$dest.error"; then
        rm -f "$dest.error"
        printf 'collected\t%s\t%s\t\n' "$logical" "${dest##*/}" >> "$MANIFEST"
    else
        detail=$(cat "$dest.error" 2>/dev/null | tr '\t\r\n' '   ')
        case "$detail" in
            *[Pp]ermission*|*denied*) status=permission_denied ;;
            *) status=read_error ;;
        esac
        rm -f "$dest"
        printf '%s\t%s\t\t%s\n' "$status" "$logical" "$detail" >> "$MANIFEST"
        rm -f "$dest.error"
    fi
}

safe_name() { printf '%s' "$1" | sed 's#[^A-Za-z0-9_.-]#_#g'; }
collect_one() {
    logical=$1
    src=$logical
    [ -z "$TEST_ROOT" ] || src="$TEST_ROOT$logical"
    name=$(safe_name "$logical")
    read_node "$src" "$OUT/$name" "$logical"
}
collect_glob() {
    logical_pattern=$1
    pattern=$logical_pattern
    [ -z "$TEST_ROOT" ] || pattern="$TEST_ROOT$logical_pattern"
    found=0
    # Shell glob expansion is bounded to the named interface patterns below.
    for path in $pattern; do
        [ -e "$path" ] || continue
        found=1
        logical=${path#"$TEST_ROOT"}
        [ -z "$TEST_ROOT" ] && logical=$path
        name=$(safe_name "$logical")
        read_node "$path" "$OUT/$name" "$logical"
    done
    if [ "$found" = 0 ]; then
        printf 'unavailable\t%s\t\tno matching interface\n' "$logical_pattern" >> "$MANIFEST"
    fi
}

# Device identity and CPU topology/policy/residency.
collect_one /sys/devices/system/cpu/online
collect_one /sys/devices/system/cpu/possible
collect_one /sys/devices/system/cpu/present
collect_one /sys/devices/system/cpu/isolated
collect_one /sys/devices/system/cpu/nohz_full
collect_glob '/sys/devices/system/cpu/cpu[0-9]*/online'
collect_glob '/sys/devices/system/cpu/cpu[0-9]*/cpufreq/*'
collect_glob '/sys/devices/system/cpu/cpu[0-9]*/core_ctl/*'
for attr in name desc latency power time usage disable; do
    collect_glob "/sys/devices/system/cpu/cpu[0-9]*/cpuidle/state[0-9]*/$attr"
done
for attr in affected_cpus related_cpus scaling_driver scaling_governor scaling_available_governors scaling_available_frequencies scaling_min_freq scaling_max_freq scaling_cur_freq cpuinfo_transition_latency cpuinfo_min_freq cpuinfo_max_freq cpuinfo_cur_freq stats/time_in_state; do
    collect_glob "/sys/devices/system/cpu/cpufreq/policy[0-9]*/$attr"
done

# KGSL / devfreq. Do not recursively traverse debugfs.
for attr in gpu_model gpuclk max_gpuclk gpubusy gpu_busy_percentage power/current_freq power/max_gpuclk power/rail_on power/gpuclk power/pwrlevel power/num_pwrlevels power/nap nap idle_timer; do
    collect_glob "/sys/class/kgsl/kgsl-3d0/$attr"
done
for attr in name governor available_frequencies available_governors cur_freq min_freq max_freq trans_stat load utilization available_power device/uevent; do
    collect_glob "/sys/class/devfreq/*/$attr"
done

# Thermal zones and cooling state/metadata.
for attr in type temp mode policy available_policies emul_temp; do
    collect_glob "/sys/class/thermal/thermal_zone[0-9]*/$attr"
done
for attr in trip_point_[0-9]*_temp trip_point_[0-9]*_type; do
    collect_glob "/sys/class/thermal/thermal_zone[0-9]*/$attr"
done
for attr in type cur_state max_state; do
    collect_glob "/sys/class/thermal/cooling_device[0-9]*/$attr"
done

# Battery and power supply values are read as reported by the device.
for attr in type status health present capacity charge_counter charge_now charge_full voltage_now voltage_avg current_now current_avg temp online scope usb_type input_current_limit constant_charge_current constant_charge_voltage; do
    collect_glob "/sys/class/power_supply/*/$attr"
done

# Memory, swap, pressure and ZRAM runtime state.
for path in /proc/meminfo /proc/vmstat /proc/zoneinfo /proc/swaps /proc/pressure/cpu /proc/pressure/memory /proc/pressure/io \
            /sys/block/zram0/disksize /sys/block/zram0/comp_algorithm /sys/block/zram0/mm_stat \
            /sys/block/zram0/io_stat /sys/block/zram0/backing_dev /sys/block/zram0/max_comp_streams; do
    collect_one "$path"
done
collect_glob '/proc/sys/kernel/sched_*'
# Android schedtune commonly appears under /dev/stune or a cgroup mount.
# Read only the controller's scalar policy files; never collect task lists.
for root in /dev/stune /sys/fs/cgroup/stune /sys/fs/cgroup/schedtune; do
    for attr in schedtune.boost schedtune.prefer_idle schedtune.sched_boost_no_override schedtune.colocate boost prefer_idle; do
        collect_glob "$root/$attr"
        collect_glob "$root/*/$attr"
    done
done
for path in /sys/devices/system/cpu/hyp_core_ctl/enable /sys/devices/system/cpu/hyp_core_ctl/status \
            /sys/kernel/debug/hyp_core_ctl/reserve_cpus; do
    collect_one "$path"
done

# Bounded block-device policy and counters for storage/I/O characterization.
collect_one /proc/diskstats
for attr in scheduler read_ahead_kb nr_requests rotational io_timeout; do
    collect_glob "/sys/block/*/queue/$attr"
done
collect_glob '/sys/block/*/stat'
collect_glob '/sys/block/*/inflight'

# Small, targeted runtime/suspend diagnostics and one bounded kernel log snapshot.
for path in /sys/power/state /sys/power/wakeup_count /sys/power/suspend_stats/success /sys/power/suspend_stats/fail /sys/power/suspend_stats/last_failed_dev \
            /sys/kernel/debug/wakeup_sources /sys/kernel/debug/suspend_stats /sys/kernel/tracing/available_events; do
    collect_one "$path"
done
if command -v dmesg >/dev/null 2>&1; then
    if dmesg > "$OUT/dmesg.txt" 2> "$OUT/dmesg.error"; then
        rm -f "$OUT/dmesg.error"
        printf 'collected\t%s\t%s\t\n' dmesg "$OUT/dmesg.txt" >> "$MANIFEST"
    else
        detail=$(cat "$OUT/dmesg.error" 2>/dev/null | tr '\t\r\n' '   ')
        printf 'permission_denied\t%s\t\t%s\n' dmesg "$detail" >> "$MANIFEST"
        rm -f "$OUT/dmesg.txt" "$OUT/dmesg.error"
    fi
else
    printf 'unavailable\t%s\t\tcommand not found\n' dmesg >> "$MANIFEST"
fi

meta collection_finished date -Iseconds
echo "Read-only collection complete: $OUT"
echo "See metadata.txt and manifest.tsv for environment and node status."
