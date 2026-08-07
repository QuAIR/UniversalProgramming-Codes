#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd -- "$script_dir/../../.." && pwd -P)"
matlab_bin="${UP_MATLAB_BIN:-matlab}"
results_root="${UP_RESULTS_ROOT:-$repo_root/results/generated}"

mkdir -p "$results_root"
export UP_RESULTS_ROOT="$results_root"

exec "$matlab_bin" -batch "run('$script_dir/run_exact_k56.m')"
