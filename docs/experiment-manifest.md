# Experiment Manifest

This manifest is the public index of experiment families in this repository.
The stable identifiers below should be used when discussing a run or artifact.
The four allowed statuses are:

- `validated`: solved with the stated residual or certificate checks;
- `diagnostic`: retained numerical evidence that is not a certified optimum;
- `legacy`: superseded or known-defective code kept for provenance;
- `incomplete`: a partial run without a validated final value.

[`results/summary.csv`](../results/summary.csv) is the source of record for
canonical numerical rows. Files under `results/diagnostic` are cross-checks or
historical evidence unless a canonical row explicitly cites one. The complete
MAT-level hashes and schemas are in
[`results/mat-artifacts.json`](../results/mat-artifacts.json).

## UP-ANALYTIC-K1

- **Status:** `validated`
- **Dimensions and copy counts:** `k=1`, `d=2,3,4,5` in the canonical table; the formula is stated for general `d` in the mathematical analysis.
- **Entry script:** None; this is the analytic formula `2d^2-3+2/d^2`.
- **Dependencies and solver:** None; analytic evaluation.
- **Sample count:** `0`.
- **Output artifacts:** [`results/summary.csv`](../results/summary.csv); the `d=2` value also has an exact SDP check in [`results/certified/kcopy_d2/exact_d2_k1.mat`](../results/certified/kcopy_d2/exact_d2_k1.mat).
- **Certificate or residual checks:** Proof of the formula; the retained `d=2` SDP record is a numerical cross-check, not the source of the analytic claim.
- **Historical source:** Manuscript analysis and source commit `45127901a920384c3f4ec56f0ecfe15b78028d0a`.
- **Known limitations:** The single-copy formula does not by itself establish a bound uniform in both `d` and `k`.

## UP-D2-EXACT-K14

- **Status:** `validated`
- **Dimensions and copy counts:** `d=2`, `k=1,2,3,4`.
- **Entry script:** [`experiments/quair06/kcopy_d2/run_exact_k14.m`](../experiments/quair06/kcopy_d2/run_exact_k14.m), calling [`src/matlab/kcopy_d2/gamma_k_d2_exact.m`](../src/matlab/kcopy_d2/gamma_k_d2_exact.m).
- **Dependencies and solver:** MATLAB, CVX, QETLAB; CVX solver selected by `UP_SDP_SOLVER`, default SDPT3.
- **Sample count:** `500` programming samples and `50` fresh-channel checks, with seeds `0` and `777`.
- **Output artifacts:** [`results/certified/kcopy_d2/exact_d2_k1.mat`](../results/certified/kcopy_d2/exact_d2_k1.mat), [`exact_d2_k2.mat`](../results/certified/kcopy_d2/exact_d2_k2.mat), [`exact_d2_k3.mat`](../results/certified/kcopy_d2/exact_d2_k3.mat), and [`exact_d2_k4.mat`](../results/certified/kcopy_d2/exact_d2_k4.mat).
- **Certificate or residual checks:** Solver status, sampled programming residual, TP residual, Hermiticity, block PSD eigenvalues, fresh-sample residual, and the `k=1` value `5.5`. Canonical `d=2,k=3,4` rows use the stronger full-space CVX-MOSEK artifacts listed under `UP-GD-CVX-CANONICAL`.
- **Historical source:** Recovered from source commit `45127901a920384c3f4ec56f0ecfe15b78028d0a` and corrected using the full row-space reduction.
- **Known limitations:** The row space is generated from finite CPTP samples. Passing fresh-channel checks is not an exact symbolic proof that every CPTP constraint is represented.

## UP-D2-K5-CANDIDATE

- **Status:** `diagnostic`
- **Dimensions and copy counts:** `d=2`, `k=5`.
- **Entry script:** Current expensive-batch definition [`experiments/quair06/kcopy_d2/run_exact_k56.m`](../experiments/quair06/kcopy_d2/run_exact_k56.m); the retained file was produced by its reconciled historical server counterpart.
- **Dependencies and solver:** MATLAB, CVX, QETLAB, SDPT3 in the retained run.
- **Sample count:** `500` programming samples and `50` fresh-channel checks.
- **Output artifacts:** [`results/diagnostic/quair06_exact_d2_k5_saved_blocks.mat`](../results/diagnostic/quair06_exact_d2_k5_saved_blocks.mat), [`results/logs/quair06_exact_k56_checkpoint.log`](../results/logs/quair06_exact_k56_checkpoint.log), and [`results/logs/quair06_exact_k56_checkpoint.csv`](../results/logs/quair06_exact_k56_checkpoint.csv).
- **Certificate or residual checks:** Saved positive and negative blocks, coefficients, `p1`, `p2`, solver status, sampled residuals, block minimum eigenvalues, TP residual, and 50 fresh-channel residuals.
- **Historical source:** Read-only quair06 snapshot reconciled on 2026-08-07; per-file source hashes are in [`docs/provenance/quair06-live-inventory.json`](provenance/quair06-live-inventory.json).
- **Known limitations:** Classification is `diagnostic_numerical_candidate`. The log contains a `linsysolve` NaN/Inf warning, and finite sample checks do not certify all-CPTP feasibility or optimality. Its value `1.35153816332987` does not replace the canonical structured value `1.350907061612`.

## UP-D2-K6-CHECKPOINT

- **Status:** `incomplete`
- **Dimensions and copy counts:** `d=2`, `k=6`.
- **Entry script:** [`experiments/quair06/kcopy_d2/run_exact_k56.m`](../experiments/quair06/kcopy_d2/run_exact_k56.m).
- **Dependencies and solver:** MATLAB, CVX, QETLAB, and a CVX SDP solver; no completed solve is retained.
- **Sample count:** The batch guard is `500` programming samples and `50` fresh-channel checks.
- **Output artifacts:** [`results/diagnostic/quair06_exact_k56_checkpoint.mat`](../results/diagnostic/quair06_exact_k56_checkpoint.mat), [`results/logs/quair06_exact_k56_checkpoint.log`](../results/logs/quair06_exact_k56_checkpoint.log), and [`results/logs/quair06_exact_k56_checkpoint.csv`](../results/logs/quair06_exact_k56_checkpoint.csv).
- **Certificate or residual checks:** None for `k=6`; the checkpoint records `NaN` and `solve_completed=false`.
- **Historical source:** Read-only quair06 snapshot reconciled on 2026-08-07.
- **Known limitations:** No `k=6` objective, feasible point, or certificate is claimed.

## UP-GD-CVX-CANONICAL

- **Status:** `validated`
- **Dimensions and copy counts:** Canonical CVX-MOSEK rows `(d,k)=(2,3),(2,4),(2,5),(3,3),(4,2),(4,3),(5,2)`.
- **Entry script:** Direct supported entries exist only for `(d,k)=(2,3),(2,4),(4,2),(5,2)`: [`cert_d2_k3.m`](../experiments/quair06/general_d/cert_d2_k3.m), [`cert_d2_k4.m`](../experiments/quair06/general_d/cert_d2_k4.m), [`cert_d4_k2.m`](../experiments/quair06/general_d/cert_d4_k2.m), and [`cert_d5_k2.m`](../experiments/quair06/general_d/cert_d5_k2.m). The exact historical parameter-specific wrappers are [`struct2_k5.m`](../legacy/server-snapshots/quair06-2026-08-07/pqga/struct2_k5.m) for `(2,5)`, [`struct2_d3k3.m`](../legacy/server-snapshots/quair06-2026-08-07/pqga/struct2_d3k3.m) for `(3,3)`, and [`struct3_d4k3.m`](../legacy/server-snapshots/quair06-2026-08-07/pqga/struct3_d4k3.m) for `(4,3)`. They are provenance snapshots, not supported launchers, and require reviewed portability adaptation before use. The portable [`gamma_struct3.m`](../experiments/quair06/general_d/gamma_struct3.m) and [`diagnostics/gamma_struct2.m`](../experiments/quair06/general_d/diagnostics/gamma_struct2.m) are implementation templates with defaults `d=2,k=5,s=500`; they are not direct reproduction scripts for the other rows.
- **Dependencies and solver:** MATLAB, CVX, QETLAB, MOSEK.
- **Sample count:** `500`; fresh checks are `200` for `d=2,k=3,4`, `50` for structured records and `d=4,k=2`, and `25` for `d=5,k=2`.
- **Output artifacts:** [`cert_d2_k3.mat`](../results/certified/general_d/cert_d2_k3.mat), [`cert_d2_k4.mat`](../results/certified/general_d/cert_d2_k4.mat), [`struct2_d2_k5.mat`](../results/certified/general_d/struct2_d2_k5.mat), [`struct2_d3_k3.mat`](../results/certified/general_d/struct2_d3_k3.mat), [`cert_d4_k2.mat`](../results/certified/general_d/cert_d4_k2.mat), [`struct3_d4_k3.mat`](../results/certified/general_d/struct3_d4_k3.mat), and [`cert_d5_k2.mat`](../results/certified/general_d/cert_d5_k2.mat).
- **Certificate or residual checks:** Depending on the formulation: full-space minimum eigenvalue, Hermiticity, TP and fresh programming residuals, or reduced-space minimum eigenvalue, non-Hermiticity, TP and fresh programming residuals. Exact fields are recorded in the MAT artifact manifest.
- **Historical source:** Source commit `45127901a920384c3f4ec56f0ecfe15b78028d0a`, historical server result trees, and the 2026-08-07 read-only reconciliation.
- **Known limitations:** No supported direct entry currently reproduces the structured `(2,5)`, `(3,3)`, or `(4,3)` artifacts. Adapting a historical wrapper requires review of paths, output isolation, dimensions, and resource use. Reduced-space finite-sample certificates are numerical and must not be described as symbolic all-CPTP proofs.

## UP-GD-YALMIP-LARGE

- **Status:** `validated`
- **Dimensions and copy counts:** Canonical rows `(d,k)=(4,4)` and `(5,3)`; additional remote MAT files cross-check `(4,3)` and `(5,2)`.
- **Entry script:** The exact historical parameter-specific wrappers are [`y3_d4k4.m`](../legacy/server-snapshots/quair06-2026-08-07/pqga/y3_d4k4.m) for `(d,k,s,n_f)=(4,4,128,12)` and [`y3_d5k3.m`](../legacy/server-snapshots/quair06-2026-08-07/pqga/y3_d5k3.m) for `(5,3,256,12)`. They are provenance snapshots, not supported launchers, and require reviewed portability adaptation before use. The portable [`gamma_y3.m`](../experiments/quair06/general_d/gamma_y3.m) is an implementation template with defaults `(d,k,s,n_f)=(2,5,500,12)` and does not directly reproduce either canonical row.
- **Dependencies and solver:** MATLAB, YALMIP, QETLAB, MOSEK.
- **Sample count:** `128` and 12 fresh checks for `d=4,k=4`; `256` and 12 fresh checks for `d=5,k=3`.
- **Output artifacts:** Canonical [`results/certified/general_d/y3_d4_k4.mat`](../results/certified/general_d/y3_d4_k4.mat) and [`y3_d5_k3.mat`](../results/certified/general_d/y3_d5_k3.mat); cross-checks [`quair06_y3_d4_k3.mat`](../results/diagnostic/quair06_y3_d4_k3.mat) and [`quair06_y3_d5_k2.mat`](../results/diagnostic/quair06_y3_d5_k2.mat).
- **Certificate or residual checks:** Reduced-space minimum eigenvalue, non-Hermiticity, TP residual, and fresh-channel programming residual.
- **Historical source:** Historical general-`d` server tree and the 2026-08-07 read-only reconciliation.
- **Known limitations:** These are memory-intensive historical runs, and no supported direct entry currently reproduces either canonical row. Cross-check MATs are diagnostic and do not create canonical rows.

## UP-GD-D3K4-POSTSOLVE

- **Status:** `diagnostic`
- **Dimensions and copy counts:** `d=3`, `k=4`.
- **Entry script:** Exact historical wrappers [`struct2_d3k4.m`](../legacy/server-snapshots/quair06-2026-08-07/pqga/struct2_d3k4.m) and [`y_d3k4.m`](../legacy/server-snapshots/quair06-2026-08-07/pqga/y_d3k4.m). They are provenance snapshots, not supported launchers, and require reviewed portability adaptation before use. The portable [`diagnostics/gamma_struct2.m`](../experiments/quair06/general_d/diagnostics/gamma_struct2.m) and [`diagnostics/gamma_y.m`](../experiments/quair06/general_d/diagnostics/gamma_y.m) retain `d=2,k=5,s=500` defaults and do not reproduce this row directly.
- **Dependencies and solver:** MATLAB, QETLAB, CVX or YALMIP, MOSEK.
- **Sample count:** `500`.
- **Output artifacts:** [`y_d3k4_postsolve_terminated.log`](../legacy/failed-runs/logs/y_d3k4_postsolve_terminated.log) and [`struct2_d3k4_postsolve_terminated.log`](../legacy/failed-runs/logs/struct2_d3k4_postsolve_terminated.log).
- **Certificate or residual checks:** Both solvers printed a completed objective and solved status, but the wrappers exited with code `143` before certificate completion.
- **Historical source:** Historical quair06 logs recovered from the general-`d` result tree.
- **Known limitations:** The canonical table retains `3.619643` only as diagnostic. No full-space or completed reduced-space certificate is available.

## UP-DIAGNOSTIC-CROSSCHECKS

- **Status:** `diagnostic`
- **Dimensions and copy counts:** Brute and Hilbert checks for `d=2,3`, mainly `k=1,2,3`; under-sampled probes include `d=2,k=3,s=300`.
- **Entry script:** Historical wrappers archived under [`legacy/general-d-baseline`](../legacy/general-d-baseline) and [`legacy/failed-runs`](../legacy/failed-runs); there is no supported aggregate launcher.
- **Dependencies and solver:** Historical MATLAB, CVX, QETLAB, usually SDPT3.
- **Sample count:** `300`, `500`, or `800`, as encoded in the filename and MAT record.
- **Output artifacts:** [`results/logs/brute_d2_k2.log`](../results/logs/brute_d2_k2.log), [`historical_results_gamma_d3_k2_s800_r1.mat`](../results/diagnostic/historical_results_gamma_d3_k2_s800_r1.mat), and [`historical_results_brute_d2_k3_s300_r0.mat`](../results/diagnostic/historical_results_brute_d2_k3_s300_r0.mat). The full set is indexed by [`results/mat-artifacts.json`](../results/mat-artifacts.json).
- **Certificate or residual checks:** Agreement of repeated objectives or solver status where recorded; these artifacts generally lack the full certificate fields.
- **Historical source:** Source commit `45127901a920384c3f4ec56f0ecfe15b78028d0a` and historical server logs.
- **Known limitations:** Under-sampled, brute, and Hilbert files are cross-check evidence. Except for the explicit canonical `d=3,k=2` artifact, they do not define rows in `results/summary.csv`.

## UP-D2-LINEAR-RELAXATION

- **Status:** `legacy`
- **Dimensions and copy counts:** `d=2`, historical `k=1,2,3,4`.
- **Entry script:** [`legacy/linear-relaxation/run_quair06_linear_k14.m`](../legacy/linear-relaxation/run_quair06_linear_k14.m).
- **Dependencies and solver:** MATLAB, CVX, QETLAB, historical CVX solver configuration.
- **Sample count:** `500`.
- **Output artifacts:** [`results/diagnostic/historical_kcopy_d2_quair06_linear_k14.mat`](../results/diagnostic/historical_kcopy_d2_quair06_linear_k14.mat) and [`quair06_full_vs_linear_k1_k3.mat`](../results/diagnostic/quair06_full_vs_linear_k1_k3.mat).
- **Certificate or residual checks:** Solver diagnostics only for the restricted `m=0,1` model.
- **Historical source:** Source commit `45127901a920384c3f4ec56f0ecfe15b78028d0a` and reconciled server snapshot.
- **Known limitations:** This is a lower-bound relaxation, is not equivalent to the full k-copy SDP, and must not be cited as `gamma_k(CPTP,2)`.

## UP-GD-DEFECTIVE-BASELINE

- **Status:** `legacy`
- **Dimensions and copy counts:** Historical general-`d` generator, used across several `d,k`; known defective for `k>=3`.
- **Entry script:** [`legacy/general-d-baseline/gamma_k.m`](../legacy/general-d-baseline/gamma_k.m) and archived generators in [`legacy/general-d-baseline/generators`](../legacy/general-d-baseline/generators).
- **Dependencies and solver:** Historical MATLAB, CVX, QETLAB; generated variants may select MOSEK.
- **Sample count:** Historical default `500`.
- **Output artifacts:** Historical diagnostic MATs under [`results/diagnostic`](../results/diagnostic) and provenance in [`docs/provenance/legacy-task-5-manifest.json`](provenance/legacy-task-5-manifest.json).
- **Certificate or residual checks:** Historical solver outputs only; no current validation is claimed.
- **Historical source:** Source commit `45127901a920384c3f4ec56f0ecfe15b78028d0a`.
- **Known limitations:** The `PermuteSystems` convention is defective for `k>=3`. The baseline is archived and unsupported.

## UP-FIXED-PROTOCOL-CHECK

- **Status:** `incomplete`
- **Dimensions and copy counts:** `d=2`, attempted `k=1,2,3`.
- **Entry script:** [`legacy/failed-runs/fixed_protocol_cost_check.m`](../legacy/failed-runs/fixed_protocol_cost_check.m).
- **Dependencies and solver:** Historical MATLAB, CVX, QETLAB, SDPT3.
- **Sample count:** The fixed-protocol script uses its historical deterministic construction rather than the supported sampled exact runner.
- **Output artifacts:** Recorded values and termination status in [`legacy/failed-runs/README.md`](../legacy/failed-runs/README.md).
- **Certificate or residual checks:** `k=1` and `k=2` printed solved values; MATLAB terminated during the attempted `k=3` run.
- **Historical source:** Recovered from a recorded server-only diagnostic; source hash is documented in the legacy provenance records.
- **Known limitations:** No `k=3` value is claimed, and the construction is not a supported upper-bound pipeline.

## UP-PBT-RECOVERED-CLAIM

- **Status:** `legacy`
- **Dimensions and copy counts:** Historical finite-`k` PBT-bound scripts over the dimensions encoded by the archived plotting program.
- **Entry script:** [`legacy/server-snapshots/quair06-2026-08-07/pqga/pbt_bound/pbt_bound.py`](../legacy/server-snapshots/quair06-2026-08-07/pqga/pbt_bound/pbt_bound.py) and [`make_fig3.py`](../legacy/server-snapshots/quair06-2026-08-07/pqga/pbt_bound/make_fig3.py).
- **Dependencies and solver:** Python and the libraries imported by the archived scripts; no SDP solve is part of this entry.
- **Sample count:** Not applicable to the recovered analytic expression.
- **Output artifacts:** Historical scripts and their [`README.md`](../legacy/server-snapshots/quair06-2026-08-07/pqga/pbt_bound/README.md).
- **Certificate or residual checks:** None performed during repository reconciliation.
- **Historical source:** Read-only quair06 snapshot reconciled on 2026-08-07.
- **Known limitations:** The scripts contain a recovered claim that was not independently re-proven. This archive does not establish the converse or the interpretation of the plotted SDP values.
