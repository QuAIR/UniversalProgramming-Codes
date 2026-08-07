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

sed_insert_before() {
    local file=$1
    local address=$2
    local text=$3
    sed_in_place "$file" "${address}i\\
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
generated_dir="${UP_RESULTS_ROOT:-$repo_root/results/generated}/legacy/general-d-baseline/generated"
OUT="$generated_dir/gamma_run_d${D}_k${K}_s${S}_r${SEED}.m"
fallback_repo_root="$(matlab_escape "$(host_to_matlab_path "$repo_root")")"

mkdir -p "$generated_dir"
cp "$script_dir/../gamma_k.m" "$OUT"
sed_in_place "$OUT" "s/^d = 2;.*/d = $D;/; s/^k = 2;.*/k = $K;/; s/^s = 500;.*/s = $S;/"
sed_in_place "$OUT" "/^method =/s/algebra/hilbert/"
# up_config obtains QETLAB from UP_QETLAB_ROOT. Prefer an explicit override while
# keeping generated, untracked scripts runnable by default.
sed_append_after "$OUT" "/^I_d/" "repo_root = getenv(\"UP_REPO_ROOT\"); if isempty(repo_root), repo_root = \"$fallback_repo_root\"; end; addpath(fullfile(repo_root, \"src\", \"matlab\")); cfg = up_config(); up_setup(cfg, false); rng($SEED);"
sed_append_after "$OUT" "/^m = bl1/" "V1=zeros(Dsec^2,bl1); for jj=1:bl1, tmp=basis_1k{jj}; V1(:,jj)=tmp(:); end; V1i=pinv(V1); A1=zeros(bl1); for jj=1:bl1, tt=transpose(basis_1k{jj}); A1(:,jj)=real(V1i*tt(:)); end; V2=zeros(Dsec^2,bl2); for jj=1:bl2, tmp=basis_k1{jj}; V2(:,jj)=tmp(:); end; V2i=pinv(V2); A2=zeros(bl2); for jj=1:bl2, tt=transpose(basis_k1{jj}); A2(:,jj)=real(V2i*tt(:)); end; Aherm=kron(A1,A2); AhermC=Aherm-eye(bl1*bl2); AhermC(abs(AhermC)<1e-9)=0;"
sed_append_after "$OUT" "/^perm(2\\*k+2) = 2\\*k+2;/" "ipm = zeros(1,2*k+2); ipm(perm) = 1:(2*k+2); perm = ipm;"
# pre-reduce all equality families to full rank (CVX 2.2 eliminate chokes on redundant rows)
sed_insert_before "$OUT" "/^cvx_begin sdp quiet/" "TPR = orth([reshape(T,[],m), -reshape(eye(dim_tp),[],1)]')'; APR=zeros(2*d^4*s,m); BPR=zeros(2*d^4*s,1); for c=1:s, Mc=reshape(P(:,:,:,c),d^4,m); rh=d*reshape(JC(:,:,c),d^4,1); APR((c-1)*2*d^4+(1:d^4),:)=real(Mc); BPR((c-1)*2*d^4+(1:d^4))=real(rh); APR((c-1)*2*d^4+d^4+(1:d^4),:)=imag(Mc); BPR((c-1)*2*d^4+d^4+(1:d^4))=imag(rh); end; RowB=orth([APR BPR]')'; ARED=RowB(:,1:end-1); BRED=RowB(:,end); AHR=orth(AhermC')'; clear APR BPR RowB;"
sed_insert_before "$OUT" "/^cvx_begin sdp quiet/" "cvx_solver mosek;"
sed_append_after "$OUT" "/minimize(p1 + p2)/" "if ~isempty(AHR); AHR*b1 == 0; AHR*b2 == 0; end; ARED*(b1-b2) == BRED; TPR*[b1;p1] == 0; TPR*[b2;p2] == 0;"
# neutralize the original redundant TP/prog constraint emissions
sed_in_place "$OUT" "s|TP1 = TP1 + b1(j) \\* T(:,:,j);||; s|TP2 = TP2 + b2(j) \\* T(:,:,j);||"
sed_in_place "$OUT" "s|TP1 == p1 \\* eye(dim_tp);||; s|TP2 == p2 \\* eye(dim_tp);||"
sed_in_place "$OUT" "s|prog = prog + (b1(j) - b2(j)) \\* P(:,:,j,c);||; s|prog == d \\* JC(:,:,c);||"
sed_in_place "$OUT" "s|J1_blk >= 0;|(J1_blk + ctranspose(J1_blk))/2 >= 0;|; s|J2_blk >= 0;|(J2_blk + ctranspose(J2_blk))/2 >= 0;|"
sed_append_after "$OUT" "/^cost = p1 + p2;/" "outputDir = fullfile(cfg.resultsRoot, \"legacy\", \"general-d-baseline\"); if exist(outputDir, \"dir\") ~= 7, mkdir(outputDir); end; save(fullfile(outputDir, sprintf(\"gamma_d%d_k%d_s%d_r%d.mat\",d,k,s,$SEED)),\"cost\",\"d\",\"k\",\"s\",\"method\",\"cvx_status\");"
printf '%s\n' "$OUT"
