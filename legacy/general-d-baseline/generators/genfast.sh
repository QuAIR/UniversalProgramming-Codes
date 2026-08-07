#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
F=$("$script_dir/gen.sh" "$@" | tail -1)
sed -i 's|PermuteSystems(kron(basis_1k{j1}, basis_k1{j2}), perm, dims_all);|PermuteSystems(kron(sparse(basis_1k{j1}), sparse(basis_k1{j2})), perm, dims_all);|' "$F"
sed -i 's|T(:,:,j) = PartialTrace(B{j}, 2\*k+2, dims_all);|T(:,:,j) = full(PartialTrace(B{j}, 2*k+2, dims_all));|' "$F"
sed -i 's|P(:,:,j,c) = PartialTrace(B{j} \* ins, 2, \[d, dk\^2, d\]);|P(:,:,j,c) = full(PartialTrace(B{j} * ins, 2, [d, dk^2, d]));|' "$F"
printf '%s\n' "$F"
