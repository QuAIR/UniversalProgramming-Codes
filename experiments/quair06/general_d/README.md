# General-Dimension Experiment Snapshots

This directory preserves the exact general-dimension server scripts recovered
from `4512790:research_code/results`, with only portable setup and output
plumbing changed. No new remote run occurred during this local-only migration.

Every MATLAB entry point resolves the repository root from its own location,
loads `src/matlab`, and calls `up_config` plus `up_setup`. Set `UP_CVX_ROOT`
and `UP_QETLAB_ROOT` for all MATLAB scripts. The YALMIP entries also require
`UP_YALMIP_ROOT`. The scripts retain their historical MOSEK solver choice;
running them requires a working MOSEK installation and license available to
the configured CVX or YALMIP environment.

Generated MAT files are written under `cfg.resultsRoot/quair06/general_d`:
`certificates` for certificate runs, `validated` for retained validated-run
snapshots, and `diagnostics` for intermediate formulations. The historical
MAT filenames are unchanged.

## Retained Validated-Run Snapshots

| Entry point | Defaults | Output or check | Dependencies |
| --- | --- | --- | --- |
| `cert_d2_k3.m` | `d=2`, `k=3`, `s=500`, `rng(0)`, 200 fresh channels with `rng(777)` | `certificates/cert_d2_k3.mat` | CVX, QETLAB, MOSEK |
| `cert_d2_k4.m` | `d=2`, `k=4`, `s=500`, `rng(0)`, 200 fresh channels with `rng(777)` | `certificates/cert_d2_k4.mat` | CVX, QETLAB, MOSEK |
| `cert_d4_k2.m` | `d=4`, `k=2`, `s=500`, `rng(0)`, 50 fresh channels with `rng(777)` | `certificates/cert_d4_k2.mat` | CVX, QETLAB, MOSEK |
| `cert_d5_k2.m` | `d=5`, `k=2`, `s=500`, `rng(0)`, 25 fresh channels with `rng(777)` | `certificates/cert_d5_k2.mat` | CVX, QETLAB, MOSEK |
| `gamma_struct3.m` | `d=2`, `k=5`, `s=500`, `rng(0)`, 50 fresh channels with `rng(777)` | `validated/struct3_d2_k5.mat` | CVX, QETLAB, MOSEK |
| `gamma_y3.m` | `d=2`, `k=5`, `s=500`, `rng(0)`, 12 fresh channels with `rng(777)` | `validated/y3_d2_k5.mat` | YALMIP, QETLAB, MOSEK |
| `validate_fastP.m` | `(d,k)=(2,2),(2,3)`, `rng(0)`, 3 test channels each | prints fast-versus-direct assembly residuals; no MAT output | CVX, QETLAB |

These are retained snapshots of historically validated runs, not a claim that
this migration reran or revalidated them. A read-only live reconciliation on
2026-08-07 matched all 148 files in the remote general-d tree to the local raw
snapshot. Seven remote-only MAT cross-checks are retained in
`results/diagnostic` without changing the canonical summary rows.

## Diagnostics

The files in `diagnostics/` are intermediate formulations or scale probes.
They retain their historical default parameters and are not primary result
entry points.

| Entry point | Defaults | Result name or behavior | Dependencies |
| --- | --- | --- | --- |
| `gamma_struct.m` | `d=2`, `k=5`, `s=500`, seeds 0 and 777, 50 fresh channels | `diagnostics/struct_d2_k5.mat` | CVX, QETLAB, MOSEK |
| `gamma_struct2.m` | `d=2`, `k=5`, `s=500`, seeds 0 and 777, 50 fresh channels | `diagnostics/struct2_d2_k5.mat` | CVX, QETLAB, MOSEK |
| `gamma_y.m` | `d=2`, `k=5`, `s=500`, seeds 0 and 777, 50 fresh channels | `diagnostics/yalmip_d2_k5.mat` | YALMIP, QETLAB, MOSEK |
| `probe_d4k4.m` | `d=4`, `k=4` | timing and memory probe; no MAT output | CVX, QETLAB |
| `fit_analytic.py` | embedded `(d,k)` values `(2,2)`, `(3,2)`, `(2,3)`, `(2,4)` | prints closed-form searches; no file output | Python with `mpmath` |

Run a MATLAB script from MATLAB with `run` and the absolute path to its entry
file. Run the Python diagnostic with `python diagnostics/fit_analytic.py`.
