#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/../../.." && pwd -P)"
results_root="${UP_RESULTS_ROOT:-$repo_root/results/generated}"
launch_dir="$results_root/server/kcopy_d2/launch"
log_file="$launch_dir/exact_k14.nohup"
pid_file="$launch_dir/exact_k14.pid"

mkdir -p "$launch_dir"
export UP_RESULTS_ROOT="$results_root"

nohup "$script_dir/run_exact_k14.sh" > "$log_file" 2>&1 &
pid=$!
printf '%s\n' "$pid" > "$pid_file"
printf '%s\n' "$pid"
