# k-copy programming cost at d=2: exact reduced SDP solver

MATLAB/CVX code for the qubit k-copy quasi-quantum programming cost
`gamma_k(CPTP, d=2)`.

The corrected exact implementation is `gamma_k_d2_exact.m`.  It uses the
SU(2) x SU(2) commutant, walled-Brauer block decomposition, and the full
k-copy programming row space followed by numerical row reduction.  This keeps
the `m=0,...,k` programming constraints.  It is not the old `m=0,1` linear
relaxation.

## Files

- `gamma_k_d2_exact.m` is the corrected exact row-space-reduced solver.
- `test_exact_api.m` checks that the exact API exists, gives
  `gamma_1(CPTP,2)=5.5`, and has three exact programming rows for `k=1`.
- `run_quair06_exact_k14.m` runs only the corrected exact SDP for
  `k=1,2,3,4` on quair06.
- `run_quair06_exact_k56.m` runs the saved-block exact batch for `k=5,6`.
- `gamma_k_d2.m` is kept as a legacy comparison implementation.  Its
  `mode='full'` path is exact for small k but constructs many redundant raw
  rows; its `mode='linear'` path is only a lower-bound relaxation.

## Mathematical status of the two modes

- `mode='full'` imposes all polarized programming rows for orders `m=0,...,k`.
  This is the exact SDP for `gamma_k`.
- `mode='linear'` keeps only the `m=0,1` rows.  It is a lower-bound relaxation,
  not an equivalent reduction in general:

```text
gamma_k(linear) <= gamma_k(full).
```

A positive `gamma_full - gamma_linear` gap means the omitted `m>=2` rows are
binding.  The updated derivation in `kcopy_d2_reduction.tex` treats the
linear model only as a diagnostic relaxation.

For the exact d=2 solver, the expected programming row ranks are:

```text
       before Hermiticity     after Hermiticity projection
k=1:          3                           3
k=2:          8                           7
k=3:         18                          16
k=4:         36                          29
```

## Requirements

MATLAB + CVX with SDPT3, SeDuMi, or MOSEK; QETLAB is also required for
`PartialTrace`, `PermuteSystems`, `RandomSuperoperator`, and related helpers.
On quair06 the working configuration is CVX with SDPT3:

```matlab
addpath('<CVX_ROOT>');
cvx_setup;
cvx_solver sdpt3;
cvx_precision high;
```

## Quick start

```matlab
addpath(pwd);
[cost, info] = gamma_k_d2_exact(1);
```

The self-test requires:

```text
gamma_k_d2_exact(1) = 5.5
```

Saved result files `exact_d2_k*.mat` include `p1`, `p2`, `coeffPlus`,
`coeffMinus`, `yPlus`, `yMinus`, `blocksPlus`, `blocksMinus`,
`blocksPlusRaw`, `blocksMinusRaw`, `blockMeta`, and `info`.

## Scaling note

The exact solver avoids the old raw multiset explosion, but the current row
space is still generated numerically from random CPTP samples and then
certified by fresh-channel residuals.  A future symbolic implementation can
replace this sampling span with explicit multiplicity-resolved Schur
intertwiner rows; it should produce the same row ranks listed above.
