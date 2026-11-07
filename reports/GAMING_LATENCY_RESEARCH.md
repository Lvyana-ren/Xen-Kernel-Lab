# Gaming, frame pacing and responsiveness research

## Source-level interaction

Interactive work passes Android input/compositor threads through scheduler wakeup/placement, WALT demand tracking, SchedTune groups, schedutil/CPUFreq and OSM, while GPU command submission and synchronization run through KGSL/Adreno and devfreq. Memory pressure and LLCC/bus votes can delay CPU/GPU work; thermal cooling can cap both. A slow frame therefore cannot be assigned to CPU or GPU from one frequency sample.

Useful source paths include `kernel/sched/core.c`, `fair.c`, `walt.c`, `tune.c`, `cpufreq_schedutil.c`, `drivers/gpu/msm/kgsl_pwrscale.c`, `kgsl_pwrctrl.c`, `drivers/devfreq/governor_msm_adreno_tz.c`, and Android's runtime task-profile/cgroup setup, which is external to this kernel checkout.

## Measurement contract

Collect raw frame timestamps or Perfetto FrameTimeline, missed/deadline frame counts, frame-time percentiles and a stated 1% low convention. Correlate a limited trace of input marker, sched_waking/wakeup/switch, CPU idle/frequency, KGSL submit/retire and thermal/cooling events. Run an untraced counterpart because tracing adds overhead. Hold display refresh/resolution/brightness, app/game version, scene, graphics options, network and temperature constant. Use at least five runs, randomized baseline/candidate order, median and spread.

## Findings

There is no actual game session, frame log, input-to-frame latency, or device trace in the current repository state. No subjective or benchmark improvement is claimed. Gaming tuning remains blocked until physical baseline and trace evidence identify whether the limiting path is CPU scheduling, GPU, memory, display, background activity or thermal policy.
