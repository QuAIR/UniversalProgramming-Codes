#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../../.." && pwd)"
D=$1
K=$2
S=${3:-500}
SEED=${4:-0}
brute_source="$script_dir/brute.m"
generated_dir="${UP_RESULTS_ROOT:-$repo_root/results/generated}/legacy/general-d-baseline/generated"
OUT="$generated_dir/brute_d${D}_k${K}_s${S}_r${SEED}.m"

if [[ ! -f "$brute_source" ]]; then
    printf '%s\n' "Missing historical provenance input: $brute_source" >&2
    exit 2
fi

mkdir -p "$generated_dir"
sed "s/^d = DVAL; k = 2; s = 500;/d = $D; k = $K; s = $S;/; s/rng(0);/rng($SEED);/" "$brute_source" > "$OUT"
sed -i "/^cost = p1 + p2;/a if ~exist(\"results\",\"dir\"); mkdir(\"results\"); end; save(sprintf(\"results/brute_d%d_k%d_s%d_r%d.mat\",d,k,s,$SEED),\"cost\",\"d\",\"k\",\"s\",\"cvx_status\");" "$OUT"
printf '%s\n' "$OUT"
