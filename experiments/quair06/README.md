# Portable Experiment Runs

These scripts define the supported exact-qubit batches and retain reviewed
general-`d` experiment snapshots. Despite the directory name, they are
portable: no hostname, account name, private path, or SSH configuration is
embedded. They can be run locally or from a checked-out repository on a
compute server.

Do not use `legacy/` scripts as substitutes for the entries documented here.
The experiment-level status and limitations are indexed in the
[experiment manifest](../../docs/experiment-manifest.md).

## Requirements

All MATLAB SDP entries require:

- MATLAB;
- CVX;
- QETLAB;
- a solver supported by the selected formulation.

The exact `d=2` code defaults to SDPT3 through CVX. General-`d` CVX snapshots
select MOSEK explicitly. YALMIP snapshots require YALMIP and MOSEK. A valid
MOSEK installation and license must already be available to CVX or YALMIP.

## Environment

The configuration layer [`up_config.m`](../../src/matlab/up_config.m) consumes:

| Variable | Used by | Default |
| --- | --- | --- |
| `UP_CVX_ROOT` | `up_setup` when CVX is not already available | empty |
| `UP_QETLAB_ROOT` | `up_setup` when QETLAB is not already available | empty |
| `UP_YALMIP_ROOT` | YALMIP entries | empty |
| `UP_MATLAB_BIN` | shell wrappers | `matlab` |
| `UP_SDP_SOLVER` | exact-qubit CVX solver selection | `sdpt3` |
| `UP_RESULTS_ROOT` | generated results, logs, PIDs, partial tables | `results/generated` |

There is no `UP_LOG_ROOT` or separate PID-root variable. Logs and PIDs are
placed below `UP_RESULTS_ROOT`, so relocating one root relocates the entire
generated run state.

Example POSIX setup with neutral installation locations:

```sh
export UP_CVX_ROOT=/opt/cvx
export UP_QETLAB_ROOT=/opt/qetlab
export UP_YALMIP_ROOT=/opt/yalmip
export UP_MATLAB_BIN=matlab
export UP_RESULTS_ROOT="$PWD/results/generated"
```

If CVX, QETLAB, or YALMIP is already initialized on the MATLAB path, its root
variable may remain unset. MATLAB callers may also pass a scalar override
structure to `up_config`.

## Exact d=2 runs

The supported solver is
[`gamma_k_d2_exact.m`](../../src/matlab/kcopy_d2/gamma_k_d2_exact.m). Both
batches enforce `sample_count=500` and `certFresh=50`; do not lower either
guard when reproducing the retained experiments.

Foreground runs:

```sh
./experiments/quair06/kcopy_d2/run_exact_k14.sh
./experiments/quair06/kcopy_d2/run_exact_k56.sh
```

Detached runs on a POSIX compute host:

```sh
./experiments/quair06/kcopy_d2/launch_exact_k14.sh
./experiments/quair06/kcopy_d2/launch_exact_k56.sh
```

The launchers print the child PID and write it below
`$UP_RESULTS_ROOT/quair06/kcopy_d2/launch/`. They do not inspect, submit to, or
terminate an external scheduler.

From an interactive MATLAB session, run either batch directly:

```matlab
run('experiments/quair06/kcopy_d2/run_exact_k14.m')
run('experiments/quair06/kcopy_d2/run_exact_k56.m')
```

### Output and resume behavior

The `k=1,...,4` and `k=5,6` batches use separate output directories. Each
batch writes:

- one MAT result per completed `k` under `per_k/`;
- a partial MAT table and CSV after every completed or failed `k`;
- a final MAT table and CSV when the loop ends;
- a MATLAB diary log.

A restarted batch skips a row only when the partial table marks it complete
and the corresponding per-`k` result passes the metadata and content checks.
The resume guard matches `d`, `k`, objective, positive and negative weights,
solver status, `sampleCount=500`, `certFresh=50`, required block variables,
and the `3e-6` numerical residual threshold. An inconsistent, stale, or corrupt
saved result causes an error. The runners do not recursively delete an output
tree, but reuse of the same root is not archival: a launcher
truncates its fixed `.nohup` log through shell redirection and replaces its PID
file, while MATLAB may rewrite partial/final MAT and CSV files, diary logs,
per-`k` results, and failed-row state. Set a new `UP_RESULTS_ROOT` before each
run when the previous run must remain byte-for-byte unchanged.

The `k=5,6` batch is substantially more expensive. Its preflight records the
basis dimension, coefficient dimension, and dense-Hermitian memory estimate.
The reconciled historical evidence contains a diagnostic `k=5` candidate and
an incomplete `k=6` checkpoint; see
[`results/README.md`](../../results/README.md) before interpreting either.

## General-d entries

The reviewed snapshots are described in
[`general_d/README.md`](general_d/README.md). The following is the one
parameter-specific supported example documented for direct reproduction:

```sh
matlab -batch "run('experiments/quair06/general_d/cert_d2_k3.m')"
```

The certificate and structured CVX scripts select MOSEK explicitly. The
YALMIP script also selects MOSEK explicitly; `UP_SDP_SOLVER` does not override
those historical choices. The portable `gamma_struct2.m`, `gamma_struct3.m`,
`gamma_y.m`, and `gamma_y3.m` files are implementation templates with
hard-coded `d=2,k=5,s=500` defaults. They are not direct launchers for the
canonical structured or YALMIP rows at other parameter values. The manifest
links the exact historical parameter-specific wrappers for provenance; those
legacy snapshots are unsupported and require reviewed portability adaptation
before use. Choose a distinct `UP_RESULTS_ROOT` before any run or parameter
change. Diagnostic entries remain diagnostic after rerunning.

Generated general-`d` MAT files are grouped under
`$UP_RESULTS_ROOT/quair06/general_d/{certificates,validated,diagnostics}`.

## Read-only reconciliation

On 2026-08-07, the two live quair06 trees were inventoried read-only and
matched against the local snapshots: 205 files, zero source SHA-256
mismatches. No remote job was started, stopped, or modified. The complete
disposition record is
[`docs/provenance/quair06-live-inventory.json`](../../docs/provenance/quair06-live-inventory.json).
This reconciliation verified provenance; it did not rerun an SDP.
