# Exact qubit batches

These are the supported d=2 qubit experiment batches. They invoke only
`gamma_k_d2_exact`, which retains the full programming-row space and writes
the block-level solution fields needed for later inspection.

`run_exact_k14.m` covers `k=1,...,4`; it verifies the `k=1` cost is 5.5 to
within `1e-5` and stops with an error if that check fails. `run_exact_k56.m`
covers `k=5,6` and records the historical memory preflight values.

All output is rooted at `cfg.resultsRoot`, which defaults to
`results/generated`. Each batch creates a per-`k` MAT file under `per_k/`,
saves a partial MAT and CSV summary after each completed value, and can resume
from that partial summary only when the corresponding per-`k` result passes
the saved metadata, block-field, 500/50-sample, status, objective, and residual
checks. A merely existing MAT file is not accepted as completed work.

Run a foreground batch through the matching shell wrapper:

```sh
experiments/quair06/kcopy_d2/run_exact_k14.sh
experiments/quair06/kcopy_d2/run_exact_k56.sh
```

The wrappers use `UP_MATLAB_BIN` when set, otherwise `matlab`; they pass
`UP_RESULTS_ROOT` through to MATLAB. The launcher variants detach a foreground
wrapper with `nohup` and store both their log and PID below the generated
output root.

MATLAB requires CVX, QETLAB, and an SDP solver. Configure their portable paths
as described in `../config/README.md`. The exact sample count is fixed at 500
and the fresh-channel certificate count is fixed at 50. No supported batch
uses the legacy linear relaxation.

## Reconciled live evidence

The live quair06 tree was reconciled read-only on 2026-08-07. All 57 files in
the qubit project matched the local snapshot SHA-256 values. No job was
running, started, stopped, or modified during the reconciliation.

The completed k=5 saved-block artifact is retained as
`results/diagnostic/quair06_exact_d2_k5_saved_blocks.mat`. It is a diagnostic
numerical candidate whose sampled constraints and checks on 50 fresh channels
pass at the recorded residual tolerances. Those finite checks do not certify
feasibility for every CPTP map, and the artifact is not an optimum; its cost
also differs from the structured result and its solver log contains a
linear-system NaN/Inf warning. The companion checkpoint records k=6 as
incomplete. These files are evidence from the historical batch, not outputs
of the supported scripts in this directory.
