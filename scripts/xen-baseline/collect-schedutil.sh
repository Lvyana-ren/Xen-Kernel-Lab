#!/system/bin/sh
# Append a read-only snapshot of active CPUFreq schedutil policy state.
set -eu
LC_ALL=C
export LC_ALL

usage() {
    echo "Usage: $0 RUN_LABEL before|during|after [OUTPUT_TSV]" >&2
    echo "Example: $0 cpu001 before /sdcard/xen-schedutil.tsv" >&2
    exit 2
}

[ "$#" -ge 2 ] && [ "$#" -le 3 ] || usage
RUN_LABEL=$1
PHASE=$2
case "$RUN_LABEL" in
    ""|*[!A-Za-z0-9_.-]*) usage ;;
esac
case "$PHASE" in
    before|during|after) ;;
    *) usage ;;
esac

STAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date +%Y-%m-%dT%H:%M:%S)
OUT_FILE=${3:-/sdcard/xen-schedutil-captures.tsv}
CPUFREQ_ROOT=${XEN_SCHEDUTIL_CPUFREQ_ROOT:-/sys/devices/system/cpu/cpufreq}
CPU_ROOT=${XEN_SCHEDUTIL_CPU_ROOT:-/sys/devices/system/cpu}
TAB=$(printf '\t')
HEADER="captured_at${TAB}device${TAB}kernel_release${TAB}run_label${TAB}phase${TAB}policy${TAB}attribute${TAB}status${TAB}value"

# Collection output must be an absolute regular file path outside kernel
# pseudo-filesystems. Reject traversal and symlinked pseudo-filesystem parents.
case "$OUT_FILE" in
    /*) ;;
    *)
        echo "Output path must be absolute: $OUT_FILE" >&2
        exit 1
        ;;
esac
case "$OUT_FILE" in
    *"/../"*|*/..)
        echo "Output path must not contain parent traversal: $OUT_FILE" >&2
        exit 1
        ;;
esac
case "$OUT_FILE" in
    /sys|/sys/*|/proc|/proc/*|/dev|/dev/*)
        echo "Refusing output path in a kernel/device pseudo-filesystem: $OUT_FILE" >&2
        exit 1
        ;;
esac
if [ -L "$OUT_FILE" ] || { [ -e "$OUT_FILE" ] && [ ! -f "$OUT_FILE" ]; }; then
    echo "Output path must be a regular, non-symlink file: $OUT_FILE" >&2
    exit 1
fi
OUT_DIR=${OUT_FILE%/*}
[ -n "$OUT_DIR" ] || OUT_DIR=/
if [ ! -d "$OUT_DIR" ]; then
    echo "Output directory must already exist: $OUT_DIR" >&2
    exit 1
fi
OUT_DIR_REAL=$(CDPATH= cd -P "$OUT_DIR" 2>/dev/null && pwd -P) || {
    echo "Cannot resolve output directory: $OUT_DIR" >&2
    exit 1
}
case "$OUT_DIR_REAL" in
    /sys|/sys/*|/proc|/proc/*|/dev|/dev/*)
        echo "Refusing output directory inside a kernel/device pseudo-filesystem: $OUT_DIR_REAL" >&2
        exit 1
        ;;
esac

if [ -s "$OUT_FILE" ]; then
    FIRST_LINE=$(head -n 1 "$OUT_FILE" 2>/dev/null || true)
    [ "$FIRST_LINE" = "$HEADER" ] || {
        echo "Existing output has an unexpected format; refusing to append: $OUT_FILE" >&2
        exit 1
    }
else
    printf '%b\n' "$HEADER" >> "$OUT_FILE" || {
        echo "Cannot initialize output file: $OUT_FILE" >&2
        exit 1
    }
fi

clean() { printf '%s' "$1" | tr '\t\r\n' '   '; }
DEVICE=$(getprop ro.product.device 2>/dev/null || true)
[ -n "$DEVICE" ] || DEVICE=unavailable
KERNEL_RELEASE=$(uname -r 2>/dev/null || echo unavailable)

record() {
    policy=$1
    attribute=$2
    status=$3
    value=$4
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
        "$STAMP" "$(clean "$DEVICE")" "$(clean "$KERNEL_RELEASE")" \
        "$RUN_LABEL" "$PHASE" "$(clean "$policy")" \
        "$(clean "$attribute")" "$status" "$(clean "$value")" >> "$OUT_FILE"
}

read_attr() {
    policy=$1
    attribute=$2
    path=$3
    if [ ! -e "$path" ]; then
        record "$policy" "$attribute" unavailable "path does not exist: $path"
    elif [ ! -r "$path" ]; then
        record "$policy" "$attribute" permission_denied "read permission check failed: $path"
    elif value=$(cat "$path" 2>&1); then
        record "$policy" "$attribute" collected "$value"
    else
        case "$value" in
            *[Pp]ermission*|*denied*) status=permission_denied ;;
            *) status=read_error ;;
        esac
        record "$policy" "$attribute" "$status" "$value"
    fi
}

policy_count=0
for policy_path in "$CPUFREQ_ROOT"/policy[0-9]*; do
    [ -d "$policy_path" ] || continue
    policy_count=$((policy_count + 1))
    policy=${policy_path##*/}

    for attribute in related_cpus affected_cpus scaling_driver scaling_governor \
        scaling_available_governors scaling_available_frequencies \
        scaling_min_freq scaling_max_freq scaling_cur_freq \
        cpuinfo_min_freq cpuinfo_max_freq cpuinfo_cur_freq \
        cpuinfo_transition_latency scaling_transition_latency; do
        read_attr "$policy" "$attribute" "$policy_path/$attribute"
    done

    governor_path="$policy_path/scaling_governor"
    if [ ! -e "$governor_path" ]; then
        governor_status=unavailable
        governor=
    elif [ ! -r "$governor_path" ]; then
        governor_status=permission_denied
        governor=
    elif governor_output=$(cat "$governor_path" 2>&1); then
        governor_status=collected
        governor=$governor_output
    else
        governor=$governor_output
        case "$governor" in
            *[Pp]ermission*|*denied*) governor_status=permission_denied ;;
            *) governor_status=read_error ;;
        esac
    fi

    if [ "$governor_status" = collected ] && [ "$governor" = schedutil ]; then
        tunables="$policy_path/schedutil"
        if [ ! -d "$tunables" ] && [ -d "$CPUFREQ_ROOT/schedutil" ]; then
            tunables="$CPUFREQ_ROOT/schedutil"
        fi
        if [ -d "$tunables" ]; then
            record "$policy" schedutil_tunable_directory collected "$tunables"
        else
            record "$policy" schedutil_tunable_directory unavailable "directory does not exist: $tunables"
        fi
        read_attr "$policy" up_rate_limit_us "$tunables/up_rate_limit_us"
        read_attr "$policy" down_rate_limit_us "$tunables/down_rate_limit_us"
    else
        if [ "$governor_status" != collected ]; then
            record "$policy" schedutil_tunable_directory "$governor_status" \
                "cannot determine active governor: $governor"
            record "$policy" up_rate_limit_us "$governor_status" \
                'cannot determine whether schedutil is active'
            record "$policy" down_rate_limit_us "$governor_status" \
                'cannot determine whether schedutil is active'
        else
            record "$policy" schedutil_tunable_directory not_active \
                "scaling_governor=$governor"
            record "$policy" up_rate_limit_us not_active \
                "scaling_governor=$governor"
            record "$policy" down_rate_limit_us not_active \
                "scaling_governor=$governor"
        fi
    fi
done

if [ "$policy_count" -eq 0 ]; then
    record none policy_directories unavailable "no policyN directories under $CPUFREQ_ROOT"
fi
read_attr global online_cpus "$CPU_ROOT/online"

echo "schedutil snapshot appended: $OUT_FILE ($RUN_LABEL / $PHASE)"
