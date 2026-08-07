#!/usr/bin/env bash
set -euo pipefail

# Both GNU sed and BSD sed accept -i with an attached backup suffix.
sed_in_place() {
    local file=$1
    shift
    sed -i.bak "$@" "$file"
    rm -f "${file}.bak"
}

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
F=$("$script_dir/gen.sh" "$@" | tail -1)
sed_in_place "$F" 's|PermuteSystems(kron(basis_1k{j1}, basis_k1{j2}), perm, dims_all);|PermuteSystems(kron(sparse(basis_1k{j1}), sparse(basis_k1{j2})), perm, dims_all);|'
sed_in_place "$F" 's|T(:,:,j) = PartialTrace(B{j}, 2\*k+2, dims_all);|T(:,:,j) = full(PartialTrace(B{j}, 2*k+2, dims_all));|'
sed_in_place "$F" 's|P(:,:,j,c) = PartialTrace(B{j} \* ins, 2, \[d, dk\^2, d\]);|P(:,:,j,c) = full(PartialTrace(B{j} * ins, 2, [d, dk^2, d]));|'
printf '%s\n' "$F"
