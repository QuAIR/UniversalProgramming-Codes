#!/usr/bin/env bash
set -euo pipefail

usage() {
    printf 'Usage: %s D K [S [SEED]]\n' "${0##*/}" >&2
    printf '%s\n' 'D, K, and S must be positive integers; SEED must be a non-negative integer.' >&2
    exit 64
}

is_positive_integer() {
    [[ $1 =~ ^[0-9]+$ && $1 != 0 ]]
}

is_nonnegative_integer() {
    [[ $1 =~ ^[0-9]+$ ]]
}

# Both GNU sed and BSD sed accept -i with an attached backup suffix.
sed_in_place() {
    local file=$1
    shift
    sed -i.bak "$@" "$file"
    rm -f "${file}.bak"
}

sed_append_after() {
    local file=$1
    local address=$2
    local text=$3
    sed_in_place "$file" "${address}a\\
${text}"
}

host_to_matlab_path() {
    local value=$1
    if command -v cygpath >/dev/null 2>&1; then
        cygpath -m "$value"
    elif command -v wslpath >/dev/null 2>&1; then
        wslpath -m "$value"
    else
        printf '%s' "$value"
    fi
}

matlab_escape() {
    local value=$1
    value=${value//\\/\\\\}
    value=${value//\"/\\\"}
    printf '%s' "$value"
}

[[ $# -ge 2 && $# -le 4 ]] || usage
D=$1
K=$2
S=${3:-500}
SEED=${4:-0}
is_positive_integer "$D" || usage
is_positive_integer "$K" || usage
is_positive_integer "$S" || usage
is_nonnegative_integer "$SEED" || usage

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../../.." && pwd)"
brute_source="$script_dir/brute.m"
generated_dir="${UP_RESULTS_ROOT:-$repo_root/results/generated}/legacy/general-d-baseline/generated"
OUT="$generated_dir/brute_d${D}_k${K}_s${S}_r${SEED}.m"
fallback_repo_root="$(matlab_escape "$(host_to_matlab_path "$repo_root")")"

if [[ ! -f "$brute_source" ]]; then
    printf '%s\n' "Missing historical provenance input: $brute_source" >&2
    exit 2
fi

mkdir -p "$generated_dir"
sed "s/^d = DVAL; k = 2; s = 500;/d = $D; k = $K; s = $S;/; s/rng(0);/rng($SEED);/" "$brute_source" > "$OUT"
sed_append_after "$OUT" "1" "legacy_repo_root = getenv(\"UP_REPO_ROOT\"); if isempty(legacy_repo_root), legacy_repo_root = \"$fallback_repo_root\"; end; addpath(fullfile(legacy_repo_root, \"src\", \"matlab\")); cfg = up_config(); up_setup(cfg, false);"
sed_append_after "$OUT" "/^cost = p1 + p2;/" "outputDir = fullfile(cfg.resultsRoot, \"legacy\", \"general-d-baseline\"); if exist(outputDir, \"dir\") ~= 7, mkdir(outputDir); end; save(fullfile(outputDir, sprintf(\"brute_d%d_k%d_s%d_r%d.mat\",d,k,s,$SEED)),\"cost\",\"d\",\"k\",\"s\",\"cvx_status\");"
printf '%s\n' "$OUT"
