#!/usr/bin/env python3
"""
irrep_dimensions.py
===================
Compute the irreducible decomposition of

    V  (x)  (V*)^{(x)k}  (x)  V^{(x)k}  (x)  V*

under SU(d), where V is the d-dimensional fundamental representation.
This is the representation space for the programmable quantum processor
with k programmer copies.

The output gives, for each SU(d) irrep lambda:
  - the SU(d) irrep dimension  s_lambda  = dim(S_lambda)
  - the multiplicity           w_lambda  = dim(W_lambda)
  - subtotal  s * w

The w_lambda values are the BLOCK SIZES in the block-diagonalized SDP.
The largest w_lambda determines computational feasibility.

Usage (plain Python 3, no SageMath needed):
    python irrep_dimensions.py 2 3      # d=2, k=3
    python irrep_dimensions.py 6 6      # d=6, k=6

For each sector B_{1,k}(d) and B_{k,1}(d) separately, and for the full
tensor product space.
"""

import sys
from math import factorial
from functools import reduce
from operator import mul
from collections import defaultdict


# =====================================================================
#  Core combinatorics
# =====================================================================

def su_reduce(partition, d):
    """Reduce a partition modulo the determinant rep for SU(d).

    For SU(d), subtracting (1,...,1) from all d rows leaves the irrep
    unchanged.  We subtract the minimum part so that the last row is 0.
    """
    lam = list(partition) + [0] * (d - len(partition))
    lam = lam[:d]
    m = min(lam)
    lam = [x - m for x in lam]
    # strip trailing zeros
    while lam and lam[-1] == 0:
        lam.pop()
    return tuple(lam)


def is_valid_partition(lam, d):
    """Check weakly decreasing with at most d parts, all non-negative."""
    if len(lam) > d:
        return False
    for i in range(len(lam)):
        if lam[i] < 0:
            return False
        if i > 0 and lam[i] > lam[i - 1]:
            return False
    return True


def _add_boxes_vertical(lam_list, remaining, start_row, chosen, results, d):
    """Recursively choose 'remaining' distinct rows to add one box each."""
    if remaining == 0:
        new_lam = list(lam_list)
        for r in chosen:
            new_lam[r] += 1
        # validity: weakly decreasing
        for i in range(len(new_lam) - 1):
            if new_lam[i] < new_lam[i + 1]:
                return
        results.append(tuple(new_lam))
        return
    for r in range(start_row, d):
        _add_boxes_vertical(lam_list, remaining - 1, r + 1,
                            chosen + [r], results, d)


def tensor_with_wedge_p(decomp, p, d):
    """Tensor a decomposition with /\\^p(V) using the Pieri rule.

    /\\^p(V) has Young diagram = single column of height p.
    Pieri rule: lambda (x) /\\^p(V) = sum over mu obtained by adding
    p boxes to lambda, at most one per row (a vertical p-strip),
    result must be a valid partition with <= d rows.

    After adding, reduce modulo det for SU(d).
    """
    new_decomp = defaultdict(int)
    for lam, mult in decomp.items():
        padded = list(lam) + [0] * (d - len(lam))
        padded = padded[:d]
        results = []
        _add_boxes_vertical(padded, p, 0, [], results, d)
        for mu in results:
            mu_red = su_reduce(mu, d)
            new_decomp[mu_red] += mult
    return dict(new_decomp)


def tensor_with_V(decomp, d):
    """Tensor with V = fundamental rep (single box)."""
    return tensor_with_wedge_p(decomp, 1, d)


def tensor_with_Vstar(decomp, d):
    """Tensor with V* = /\\^{d-1}(V) for SU(d)."""
    if d == 1:
        return dict(decomp)  # trivial
    return tensor_with_wedge_p(decomp, d - 1, d)


# =====================================================================
#  Weyl dimension formula for SU(d)
# =====================================================================

def su_dim(partition, d):
    """Dimension of the SU(d) irrep labeled by partition lambda.

    Uses Weyl's formula:
      dim = prod_{1<=i<j<=d} (l_i - l_j + j - i) / (j - i)
    where l is the partition padded to d parts.
    """
    lam = list(partition) + [0] * (d - len(partition))
    lam = lam[:d]
    num = 1
    den = 1
    for i in range(d):
        for j in range(i + 1, d):
            num *= (lam[i] - lam[j] + j - i)
            den *= (j - i)
    return num // den


# =====================================================================
#  Decomposition of mixed tensor products
# =====================================================================

def decompose_mixed_tensor(d, r, s):
    """Decompose V^{(x)r} (x) (V*)^{(x)s} under SU(d).

    Returns dict: { partition : multiplicity }.
    """
    if d == 1:
        return {(): 1}

    # Start with trivial rep
    decomp = {(): 1}

    # Tensor with V, r times
    for _ in range(r):
        decomp = tensor_with_V(decomp, d)

    # Tensor with V*, s times
    for _ in range(s):
        decomp = tensor_with_Vstar(decomp, d)

    return decomp


# =====================================================================
#  Pretty printing
# =====================================================================

def print_decomposition(label, decomp, d):
    """Pretty-print an irrep decomposition."""
    print()
    print('=' * 65)
    print(f'  {label}')
    print('=' * 65)
    print(f'  {"Partition":>25s}  {"s (SU dim)":>10s}  {"w (mult)":>10s}  {"s*w":>8s}')
    print(f'  {"-" * 60}')

    total = 0
    max_w = 0
    total_w2 = 0
    items = []
    for lam, mult in decomp.items():
        s_dim = su_dim(lam, d)
        items.append((s_dim, mult, lam))
        total += s_dim * mult
        max_w = max(max_w, mult)
        total_w2 += mult ** 2

    # Sort by multiplicity descending, then su_dim descending
    items.sort(key=lambda x: (-x[1], -x[0]))

    for s_dim, mult, lam in items:
        lam_str = str(lam) if lam else '()'
        print(f'  {lam_str:>25s}  {s_dim:>10d}  {mult:>10d}  {s_dim * mult:>8d}')

    print(f'  {"-" * 60}')
    print(f'  {"TOTAL":>25s}  {"":>10s}  {"":>10s}  {total:>8d}')
    print(f'  Number of blocks: {len(items)}')
    print(f'  Largest block w : {max_w}')
    print(f'  Sum of w^2      : {total_w2}  (= number of SDP variables per Ji)')


def analyze_full_space(d, k):
    """Analyze the full tensor product space for the programmable processor.

    Symmetry:  J -> (U (x) (Ubar (x) V)^{(x)k} (x) Vbar) J (...)^dag
    where U, V are INDEPENDENT SU(d) elements.

    This is SU(d)_U x SU(d)_V acting on two sectors:
      Sector 1 (SU(d)_U): S(U) (x) Ubar_1 (x) ... (x) Ubar_k  =  V (x) (V*)^k
      Sector 2 (SU(d)_V): V_1 (x) ... (x) V_k (x) S'(Vbar)    =  V^k (x) V*

    By Schur's lemma for the product group, blocks are labeled by pairs
    (lambda, mu) with block size  w1_lambda * w2_mu.
    """
    print()
    print('#' * 65)
    print(f'  d = {d},  k = {k}')
    print(f'  Full space dim = d^(2k+2) = {d}^{2 * k + 2} = {d ** (2 * k + 2)}')
    print(f'  Symmetry: SU(d)_U x SU(d)_V  (independent U, V)')
    print('#' * 65)

    # --- Sector 1: SU(d)_U on V (x) (V*)^k ---
    print('\n--- Sector 1 [SU(d)_U]:  V (x) (V*)^k    [B_{1,k}(d)] ---')
    decomp1 = decompose_mixed_tensor(d, 1, k)
    print_decomposition(f'V (x) (V*)^{k}  under SU({d})_U', decomp1, d)

    # --- Sector 2: SU(d)_V on V^k (x) V* ---
    print('\n--- Sector 2 [SU(d)_V]:  V^k (x) V*    [B_{k,1}(d)] ---')
    decomp2 = decompose_mixed_tensor(d, k, 1)
    print_decomposition(f'V^{k} (x) V*  under SU({d})_V', decomp2, d)

    # --- Full space under SU(d)_U x SU(d)_V ---
    # Blocks are tensor products: (lambda, mu) with size w1_lam * w2_mu
    w1_list = sorted(decomp1.values(), reverse=True)
    w2_list = sorted(decomp2.values(), reverse=True)
    n1 = len(decomp1)
    n2 = len(decomp2)
    n_blocks = n1 * n2

    # Compute block sizes for all pairs
    block_sizes = []
    for lam, w1 in decomp1.items():
        s1 = su_dim(lam, d)
        for mu, w2 in decomp2.items():
            s2 = su_dim(mu, d)
            block_sizes.append((w1 * w2, s1 * s2, lam, mu))
    block_sizes.sort(key=lambda x: -x[0])

    # Verify total dimension
    total_dim = sum(w * s for w, s, _, _ in block_sizes)
    expected = d ** (2 * k + 2)

    print(f'\n--- Full space under SU({d})_U x SU({d})_V ---')
    print()
    print('=' * 80)
    print(f'  Block structure:  {n1} x {n2} = {n_blocks} blocks  (pairs (lambda, mu))')
    print('=' * 80)
    print(f'  {"(lambda, mu)":>45s}  {"s1*s2":>8s}  {"w1*w2":>8s}  {"total":>10s}')
    print(f'  {"-" * 75}')

    max_w = 0
    sum_w2 = 0
    # Show top 20 blocks
    for i, (w, s, lam, mu) in enumerate(block_sizes):
        max_w = max(max_w, w)
        sum_w2 += w ** 2
        if i < 20:
            lam_s = str(lam) if lam else '()'
            mu_s = str(mu) if mu else '()'
            pair_s = f'({lam_s}, {mu_s})'
            print(f'  {pair_s:>45s}  {s:>8d}  {w:>8d}  {w * s:>10d}')
    if len(block_sizes) > 20:
        print(f'  {"... (" + str(len(block_sizes) - 20) + " more blocks)":>45s}')

    print(f'  {"-" * 75}')
    print(f'  {"TOTAL":>45s}  {"":>8s}  {"":>8s}  {total_dim:>10d}')
    if total_dim != expected:
        print(f'  *** DIMENSION MISMATCH: expected {expected} ***')
    else:
        print(f'  (matches d^(2k+2) = {expected})')

    # --- Summary ---
    # Also compute the alternative: sum of w1^2 * w2^2 = (sum w1^2)(sum w2^2)
    sum_w1_sq = sum(v ** 2 for v in decomp1.values())
    sum_w2_sq = sum(v ** 2 for v in decomp2.values())

    print()
    print('=' * 80)
    print(f'  SUMMARY for d={d}, k={k}   [SU(d) x SU(d) symmetry]')
    print('=' * 80)
    print(f'  Full space dimension      : {expected}')
    print(f'  Sector 1 blocks           : {n1}   (max w1 = {max(decomp1.values())})')
    print(f'  Sector 2 blocks           : {n2}   (max w2 = {max(decomp2.values())})')
    print(f'  Total block pairs         : {n_blocks}')
    print(f'  Largest block (max w1*w2) : {max_w}')
    print(f'  SDP vars per Ji           : {sum_w2}  (sum of (w1*w2)^2)')
    print(f'    = (sum w1^2)*(sum w2^2)  = {sum_w1_sq} * {sum_w2_sq} = {sum_w1_sq * sum_w2_sq}')
    print(f'  Original SDP variables    : {d ** (2 * (2 * k + 2))}  (D^2)')
    print(f'  Reduction factor          : {d ** (2 * (2 * k + 2)) / sum_w2:.1f}x')
    print('=' * 80)


if __name__ == '__main__':
    d_val = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    k_val = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    analyze_full_space(d_val, k_val)
