# UniversalProgramming-Codes

Reproducibility package for the semidefinite programs used to study universal
programming of quantum channels. The reported objective is the programming
cost `gamma_k(CPTP,d)`: the minimum quasiprobability overhead for a processor
programmed by `k` copies of a channel state. It is not a unitary-inversion
fidelity.

## Status legend

| Status | Meaning |
| --- | --- |
| **validated** | A solved value with the residual or certificate checks named in the experiment manifest. |
| **diagnostic** | Useful numerical evidence or a cross-check, but not a reportable certified optimum. |
| **legacy** | Superseded or known-defective code retained only for provenance. |
| **incomplete** | A partial run or checkpoint without a validated final value. |

Only `src/` and the explicitly supported entries under `experiments/` are
current implementations. Do not run scripts from `legacy/` as supported
experiments. In particular, the archived general-`d` baseline has a known
subsystem-permutation defect for `k >= 3`, and the archived qubit linear model
is a lower-bound relaxation that is not equivalent to the exact SDP.

## Quick start: exact qubit k=1

Requirements are MATLAB, CVX, QETLAB, and an SDP solver supported by CVX. The
default supported solver is SDPT3. From the repository root, configure paths
in the environment if CVX and QETLAB are not already on the MATLAB path:

```powershell
$env:UP_CVX_ROOT = "C:\path\to\cvx"
$env:UP_QETLAB_ROOT = "C:\path\to\QETLAB"
$env:UP_SDP_SOLVER = "sdpt3"
matlab -batch "addpath('src/matlab'); cfg=up_config(); up_setup(cfg,false); opts=struct('setupCvx',false,'solver',cfg.solver,'s',500,'certFresh',50,'saveResult',false); [g,info]=gamma_k_d2_exact(1,opts); fprintf('gamma_1(CPTP,2)=%.12f\n',g); assert(abs(g-5.5)<1e-5)"
```

The expected objective is `5.500000`. The solver constructs the programming
row space from 500 sampled CPTP maps and checks 50 fresh samples. These finite
checks are numerical evidence; they are not an exact symbolic certification
of the full polynomial row space.

## Strict submultiplicativity example

The historical two-channel qubit example, its 360-entry sparse rational
correction matrix, and a compact MATLAB checker are collected in
[`experiments/strict_submultiplicativity`](experiments/strict_submultiplicativity).
The default entry reconstructs the correction and checks its Hermiticity,
trace-annihilation, and four program-pair annihilation identities. A full CVX
norm recomputation is available as an optional, more expensive mode.

## Repository layout

| Path | Contents |
| --- | --- |
| [`src/matlab`](src/matlab) | Supported common routines, portable configuration, and the corrected exact qubit solver. |
| [`experiments/quair06`](experiments/quair06) | Portable batch definitions and general-`d` experiment snapshots. |
| [`experiments/strict_submultiplicativity`](experiments/strict_submultiplicativity) | Finite-qubit strict-submultiplicativity example and historical correction checker. |
| [`results`](results) | Canonical table, retained MAT evidence, logs, and the machine-readable artifact manifest. |
| [`docs/experiment-manifest.md`](docs/experiment-manifest.md) | Status, entry point, dependencies, artifacts, checks, source, and limitations for each experiment family. |
| [`docs/mathematical-reduction`](docs/mathematical-reduction) | Corrected reduction and its implementation map. |
| [`docs/provenance`](docs/provenance) | Git and read-only quair06 reconciliation records. |
| [`legacy`](legacy) | Defective, relaxed, failed, superseded, or historical-only code. |
| [`tests`](tests) | Static, evidence-loading, configuration, and inexpensive numerical checks. |

## Configuration

`src/matlab/up_config.m` consumes the following variables. Command-line shell
wrappers also consume `UP_MATLAB_BIN`.

| Variable | Purpose | Default |
| --- | --- | --- |
| `UP_CVX_ROOT` | CVX installation root | empty; CVX may already be on the MATLAB path |
| `UP_QETLAB_ROOT` | QETLAB installation root | empty; QETLAB may already be on the MATLAB path |
| `UP_YALMIP_ROOT` | YALMIP installation root for YALMIP experiments | empty |
| `UP_MATLAB_BIN` | MATLAB executable used by shell wrappers | `matlab` |
| `UP_SDP_SOLVER` | solver passed to the exact qubit CVX program | `sdpt3` |
| `UP_RESULTS_ROOT` | generated-output root | `results/generated` |

MOSEK and YALMIP are optional for the exact qubit quick start. They are
required only by the general-`d` entries that name them. MOSEK must be
installed and licensed through the selected CVX or YALMIP environment. There
is no `UP_LOG_ROOT`: batch logs live below `UP_RESULTS_ROOT`.

See the [portable run guide](experiments/quair06/README.md) for foreground,
detached, resume, and general-`d` examples.

## Batch examples

Run the supported exact qubit batches from a POSIX shell:

```sh
export UP_CVX_ROOT=/opt/cvx
export UP_QETLAB_ROOT=/opt/qetlab
export UP_RESULTS_ROOT="$PWD/results/generated"
./experiments/quair06/kcopy_d2/run_exact_k14.sh
./experiments/quair06/kcopy_d2/launch_exact_k56.sh
```

The first command runs `k=1,...,4` in the foreground. The second launches the
expensive `k=5,6` batch, writes a PID and log below `UP_RESULTS_ROOT`, and
resumes only from completed per-`k` records. Neither runner recursively deletes
an output tree, but reuse of one root can truncate the fixed launcher log,
replace its PID file, and rewrite MAT, CSV, diary, per-`k`, or failed-row state.
Use a new `UP_RESULTS_ROOT` to preserve a previous run unchanged. Both batches
preserve `sample_count=500` and `certFresh=50`.

## Canonical numerical results

This table is checked against [`results/summary.csv`](results/summary.csv),
which is the machine-readable source of record. `d=3,k=2` and `d=3,k=4`
remain diagnostic; all other listed rows are classified as validated under the
checks stated in the [experiment manifest](docs/experiment-manifest.md).

<!-- canonical-summary:start -->
| d | k | gamma | status |
| ---: | ---: | ---: | --- |
| 2 | 1 | 5.500000 | validated |
| 2 | 2 | 2.713330 | validated |
| 2 | 3 | 1.888291 | validated |
| 2 | 4 | 1.529423 | validated |
| 2 | 5 | 1.350907 | validated |
| 3 | 1 | 15.222222 | validated |
| 3 | 2 | 7.456450 | diagnostic |
| 3 | 3 | 4.882170 | validated |
| 3 | 4 | 3.619643 | diagnostic |
| 4 | 1 | 29.125000 | validated |
| 4 | 2 | 14.366215 | validated |
| 4 | 3 | 9.453850 | validated |
| 4 | 4 | 7.003853 | validated |
| 5 | 1 | 47.080000 | validated |
| 5 | 2 | 23.324402 | validated |
| 5 | 3 | 15.410364 | validated |
<!-- canonical-summary:end -->

The additional exact-qubit `k=5` saved-block result is retained only as a
`diagnostic_numerical_candidate`. Its sampled and 50-fresh-channel residuals
pass at the recorded tolerances, but they do not certify feasibility for all
CPTP maps or optimality. The corresponding `k=6` checkpoint is incomplete.
Neither replaces the canonical `d=2,k=5` row above.

## Verification

The complete Python suite and static verifier are dependency-light:

```sh
python -m unittest discover -s tests/python -p "test_*.py"
python tools/verify_repository.py
```

The static verifier scans JSON as well as source and documentation, checks the
MAT inventory hashes and declared schemas, and cross-checks MAT-backed summary
rows. MATLAB performs the actual variable-level schema and numerical residual
checks.

MATLAB evidence and configuration checks load retained files but do not solve
the large SDPs:

```matlab
run('tests/matlab/test_paths.m')
run('tests/matlab/test_portable_configuration.m')
run('tests/matlab/test_result_artifacts.m')
run('tests/matlab/test_quair06_evidence.m')
```

`tests/matlab/smoke_k1.m` is the optional solver-backed `k=1` check.

## Provenance and licensing

The quair06 trees were reconciled read-only on 2026-08-07: 57 files from the
qubit tree and 148 from the general-`d` tree, for 205 files total and zero
source SHA-256 mismatches. No remote job was started, stopped, or modified.
Remote modification times were captured read-only on 2026-08-08 and normalized
to UTC after access was restored; the source hashes remained unchanged.
See the [live inventory](docs/provenance/quair06-live-inventory.json), the
[artifact manifest](results/mat-artifacts.json), and the
[provenance notes](docs/provenance/README.md).

No license has been specified for this repository. Contact the repository
owners before reuse or redistribution beyond inspection and reproducibility
review.
