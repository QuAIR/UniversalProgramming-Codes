#!/usr/bin/env bash
set -o pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../.." && pwd)"
results_root="${UP_RESULTS_ROOT:-$repo_root/results/generated}"
output_dir="$results_root/legacy/qubit-reduced-prototype"
matlab_bin="${UP_MATLAB_BIN:-matlab}"

mkdir -p "$output_dir"
export UP_RESULTS_ROOT="$results_root"
cd "$script_dir"
"$matlab_bin" -batch run_quair06_k14 2>&1 | tee "$output_dir/kcopy_d2_updated_k14.log"
status=${PIPESTATUS[0]}
printf 'EXIT_CODE=%s\n' "$status" >> "$output_dir/kcopy_d2_updated_k14.log"
exit "$status"
