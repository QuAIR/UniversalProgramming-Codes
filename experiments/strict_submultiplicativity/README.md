# Finite-Qubit Strict Submultiplicativity Example

This directory restores the finite-channel example used to demonstrate that
the programming cost can be strictly submultiplicative under tensor products.
It is intended as the public code-and-data target for the corresponding
manuscript statement.

Stable GitHub link:
[strict-submultiplicativity example](https://github.com/QuAIR/UniversalProgramming-Codes/tree/main/experiments/strict_submultiplicativity).

## Channel Set

The set `S_sub` contains two qubit channels. Both have Kraus operators

```text
K1 = [0 sqrt(g); 0 0]
K2 = [1 0; 0 sqrt(alpha)]
K3 = [0 0; 0 sqrt(lambda)]
```

with parameters

```text
(g, alpha, lambda) = (4/9, 4/9, 1/9)
(g, alpha, lambda) = (4/9, 1/9, 4/9).
```

The normalized program state is `pi_E = J_E/2`. The historical correction
matrix `J_C` has size `256 x 256` and register order

```text
S1,S2,A1,A2,B1,B2,S1_out,S2_out.
```

Its 360 nonzero rational entries are stored in
[`../../results/certified/strict_submult_C_sparse.tsv`](../../results/certified/strict_submult_C_sparse.tsv).

## Run

Requirements for the default check are MATLAB and QETLAB. Configure QETLAB if
it is not already on the MATLAB path:

```powershell
$env:UP_QETLAB_ROOT = "C:\path\to\QETLAB"
matlab -batch "run('experiments/strict_submultiplicativity/run_strict_submultiplicativity.m')"
```

The script reconstructs `J_C` and reports:

- channel trace-preservation residuals;
- Hermiticity of `J_C`;
- the output partial trace of `J_C`;
- the four program-pair annihilation residuals.

For the retained data, the largest annihilation residual is approximately
`7.7e-18` in double precision.

The optional full numerical recomputation additionally requires CVX:

```matlab
addpath('experiments/strict_submultiplicativity')
report = verify_strict_submultiplicativity(struct('solve', true));
```

This solves the one-copy processor SDP, forms the correlated processor
`P_tensor + C`, and calls QETLAB's fixed-map diamond-norm routine. Depending on
the CVX solver, this optional step can be substantially more expensive than the
default certificate-data check.

## Evidence Boundary

The sparse rational matrix exactly records the historical correction data, and
the default script verifies its structural identities up to floating-point
roundoff. The TSV does not contain the original one-copy primal solution or
matching primal-dual rational bounds for the strict norm gap. It must therefore
not be described by itself as a complete rigorous primal-dual certificate of
the strict inequality. The example and its strict gap were checked numerically
in the original project; the code here makes the retained construction directly
inspectable and reproducible.

## Provenance

The channel definition appears in the local manuscript history. The correction
was first stored as `anc/C_strict_submult.txt` in commit `b73a1de` and later as
`certificates/strict_submult_C_sparse.tsv` in commit `e1af873`. The more explicit
manuscript description is retained in Overleaf-history commit `dc58b12`.
