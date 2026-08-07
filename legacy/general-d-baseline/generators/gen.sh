#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../../.." && pwd)"
D=$1
K=$2
S=${3:-500}
SEED=${4:-0}
generated_dir="${UP_RESULTS_ROOT:-$repo_root/results/generated}/legacy/general-d-baseline/generated"
OUT="$generated_dir/gamma_run_d${D}_k${K}_s${S}_r${SEED}.m"

mkdir -p "$generated_dir"
cp "$script_dir/../gamma_k.m" "$OUT"
sed -i "s/^d = 2;.*/d = $D;/; s/^k = 2;.*/k = $K;/; s/^s = 500;.*/s = $S;/" "$OUT"
sed -i "/^method =/s/algebra/hilbert/" "$OUT"
# up_config obtains QETLAB from UP_QETLAB_ROOT and keeps generated code portable.
sed -i "/^I_d/a repo_root = getenv(\"UP_REPO_ROOT\"); if isempty(repo_root), error(\"legacy:missingRepoRoot\", \"Set UP_REPO_ROOT before running generated scripts.\"); end; addpath(fullfile(repo_root, \"src\", \"matlab\")); cfg = up_config(); up_setup(cfg, false); rng($SEED);" "$OUT"
sed -i "/^m = bl1/a V1=zeros(Dsec^2,bl1); for jj=1:bl1, tmp=basis_1k{jj}; V1(:,jj)=tmp(:); end; V1i=pinv(V1); A1=zeros(bl1); for jj=1:bl1, tt=transpose(basis_1k{jj}); A1(:,jj)=real(V1i*tt(:)); end; V2=zeros(Dsec^2,bl2); for jj=1:bl2, tmp=basis_k1{jj}; V2(:,jj)=tmp(:); end; V2i=pinv(V2); A2=zeros(bl2); for jj=1:bl2, tt=transpose(basis_k1{jj}); A2(:,jj)=real(V2i*tt(:)); end; Aherm=kron(A1,A2); AhermC=Aherm-eye(bl1*bl2); AhermC(abs(AhermC)<1e-9)=0;" "$OUT"
sed -i "/^perm(2\*k+2) = 2\*k+2;/a ipm = zeros(1,2*k+2); ipm(perm) = 1:(2*k+2); perm = ipm;" "$OUT"
# pre-reduce all equality families to full rank (CVX 2.2 eliminate chokes on redundant rows)
sed -i "/^cvx_begin sdp quiet/i TPR = orth([reshape(T,[],m), -reshape(eye(dim_tp),[],1)]')'; APR=zeros(2*d^4*s,m); BPR=zeros(2*d^4*s,1); for c=1:s, Mc=reshape(P(:,:,:,c),d^4,m); rh=d*reshape(JC(:,:,c),d^4,1); APR((c-1)*2*d^4+(1:d^4),:)=real(Mc); BPR((c-1)*2*d^4+(1:d^4))=real(rh); APR((c-1)*2*d^4+d^4+(1:d^4),:)=imag(Mc); BPR((c-1)*2*d^4+d^4+(1:d^4))=imag(rh); end; RowB=orth([APR BPR]')'; ARED=RowB(:,1:end-1); BRED=RowB(:,end); AHR=orth(AhermC')'; clear APR BPR RowB;" "$OUT"
sed -i "/^cvx_begin sdp quiet/i cvx_solver mosek;" "$OUT"
sed -i "/minimize(p1 + p2)/a if ~isempty(AHR); AHR*b1 == 0; AHR*b2 == 0; end; ARED*(b1-b2) == BRED; TPR*[b1;p1] == 0; TPR*[b2;p2] == 0;" "$OUT"
# neutralize the original redundant TP/prog constraint emissions
sed -i "s|TP1 = TP1 + b1(j) \* T(:,:,j);||; s|TP2 = TP2 + b2(j) \* T(:,:,j);||" "$OUT"
sed -i "s|TP1 == p1 \* eye(dim_tp);||; s|TP2 == p2 \* eye(dim_tp);||" "$OUT"
sed -i "s|prog = prog + (b1(j) - b2(j)) \* P(:,:,j,c);||; s|prog == d \* JC(:,:,c);||" "$OUT"
sed -i "s|J1_blk >= 0;|(J1_blk + ctranspose(J1_blk))/2 >= 0;|; s|J2_blk >= 0;|(J2_blk + ctranspose(J2_blk))/2 >= 0;|" "$OUT"
sed -i "/^cost = p1 + p2;/a if ~exist(\"results\",\"dir\"); mkdir(\"results\"); end; save(sprintf(\"results/gamma_d%d_k%d_s%d_r%d.mat\",d,k,s,$SEED),\"cost\",\"d\",\"k\",\"s\",\"method\",\"cvx_status\");" "$OUT"
printf '%s\n' "$OUT"
