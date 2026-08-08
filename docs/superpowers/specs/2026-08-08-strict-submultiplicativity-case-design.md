# Strict Submultiplicativity Case Design

## Purpose

Restore the finite qubit strict-submultiplicativity example as a supported,
reader-facing MATLAB experiment. The repository already contains the historical
sparse rational correction matrix, but it does not contain the MATLAB program
that reconstructs the example or recomputes the numerical norm gap.

The restored experiment must distinguish exact certificate-data checks from
solver-dependent numerical evidence. The existing TSV file is not a complete
primal-dual rational certificate for the strict inequality.

## Mathematical Input

Let `S_sub` contain two qubit channels. Both use Kraus operators

```text
K1 = [0 sqrt(g); 0 0]
K2 = [1 0; 0 sqrt(alpha)]
K3 = [0 0; 0 sqrt(lambda)]
```

with parameter triples

```text
(g, alpha, lambda) = (4/9, 4/9, 1/9)
(g, alpha, lambda) = (4/9, 1/9, 4/9).
```

The historical correction is the `256 x 256` Choi matrix `J_C` stored in
`results/certified/strict_submult_C_sparse.tsv`. Its register order is

```text
S1, S2, A1, A2, B1, B2, S1_out, S2_out.
```

Here `A_i,B_i` carry the normalized Choi program state for channel `i`.

## User Interface

The supported entry point is
`experiments/strict_submultiplicativity/run_strict_submultiplicativity.m`.
The computational API is
`verify_strict_submultiplicativity(opts)`, which returns a scalar `report`
structure.

Two modes are supported:

- Structural mode loads the TSV and checks the channel and correction data.
  It does not require CVX or QETLAB.
- Full mode additionally uses CVX to solve the one-copy processor SDP, forms
  the correlated two-copy processor, computes its quasiprobability cost, and
  reports the numerical strict-submultiplicativity gap.

The runner uses full mode. Tests use structural mode so routine repository
checks remain inexpensive.

## Components

### Certificate loader

`load_strict_submult_certificate.m` reads the TSV with MATLAB's tabular import
API, validates its four-column schema, one-based indices, dimensions, unique
locations, nonzero rational entries, and count, then reconstructs a sparse
matrix before returning a full Hermitian matrix for numerical contractions.

### Structural verifier

`verify_strict_submultiplicativity.m` constructs the two normalized Choi
states and checks:

- each Kraus family is trace preserving;
- `J_C` is Hermitian;
- tracing out the two output registers gives zero;
- the induced map vanishes for each of the four product program states.

The verifier contains small local tensor-permutation and partial-trace helpers
so structural mode has no external toolbox dependency.

### Solver-backed verifier

Full mode solves the one-copy programming SDP over a Hermiticity-preserving,
trace-preserving processor. It then permutes the Choi matrix of the tensor-square
processor into the certificate register order and defines

```text
J_hat = J_product + J_C.
```

A second fixed-map SDP computes the minimum positive-minus-negative CPTP
decomposition cost of `J_hat`. The report includes the one-copy cost, its
square, the correlated cost, the strict gap, CVX statuses, trace-preservation
residuals, and programming residuals.

The numerical conclusion is accepted only when both CVX solves report a solved
status, all declared residuals meet tolerance, and the strict gap exceeds the
configured gap tolerance.

## Documentation

The experiment README explains the channel set, register order, certificate
format, exact-versus-numerical evidence boundary, dependencies, commands, and
report fields. The root README, experiment manifest, and certified-results
README link to the independent case.

Documentation must use the phrase "reproducible numerical
strict-submultiplicativity example" and must not describe the TSV alone as a
complete rigorous certificate of the strict norm inequality.

## Testing

Development follows a red-green cycle:

1. Add a MATLAB test that expects the loader and structural API to exist and
   verifies the certificate count, register order, channel trace preservation,
   Hermiticity, output partial trace, and four annihilation residuals.
2. Run it and confirm failure because the new API is absent.
3. Implement the minimum structural API and rerun until it passes.
4. Add static Python assertions for repository links and evidence-language
   boundaries, confirm their initial failure, then update the documentation.
5. Run the full solver-backed example and record its actual numerical output in
   the experiment README only after a successful run.

## Error Handling

The MATLAB API raises named errors for malformed options, missing certificate
data, invalid TSV schema or entries, unavailable CVX in full mode, unsuccessful
solver status, failed residual checks, or a missing numerical strict gap.
Structural mode never silently falls back to a solver-backed claim.

## Out Of Scope

- Producing a new exact primal-dual rational certificate.
- Modifying the manuscript's current treatment of submultiplicativity.
- Generalizing the example beyond the two historical qubit channels.
- Adding Python or CVXPY as a numerical dependency.
