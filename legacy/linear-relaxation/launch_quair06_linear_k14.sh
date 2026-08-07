#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../.." && pwd)"
results_root="${UP_RESULTS_ROOT:-$repo_root/results/generated}"
output_dir="$results_root/legacy/linear-relaxation"

mkdir -p "$output_dir"
export UP_RESULTS_ROOT="$results_root"
nohup "$script_dir/run_quair06_linear_k14.sh" > "$output_dir/kcopy_d2_linear_k14.nohup" 2>&1 < /dev/null &
pid=$!
printf '%s\n' "$pid" > "$output_dir/kcopy_d2_linear_k14.pid"
printf '%s\n' "$pid"
