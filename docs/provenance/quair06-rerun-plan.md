# quair06 Reconciliation and Rerun Note

The live quair06 reconciliation was completed read-only on 2026-08-07. The 57
files in the qubit tree and 148 files in the general-d tree matched the local
snapshot source hashes, for 205 files and zero SHA-256 mismatches. No remote
job was started, stopped, or modified. The per-file record is
[`quair06-live-inventory.json`](quair06-live-inventory.json).

The reconciliation recovered a completed exact-qubit `k=5` saved-block file
and a `k=5,6` checkpoint. The former is classified only as a diagnostic
numerical candidate; the latter records `k=6` as incomplete. See
[`../../results/README.md`](../../results/README.md) and the
[`../experiment-manifest.md`](../experiment-manifest.md) for the checks and
limitations.

Future exact `d=2`, `k=5,6` runs should use
[`../../experiments/quair06/kcopy_d2/run_exact_k56.m`](../../experiments/quair06/kcopy_d2/run_exact_k56.m),
preserve `opts.s=500` and `opts.certFresh=50`, and write to a new
`UP_RESULTS_ROOT`. A rerun is a new experiment and must not overwrite the
reconciled evidence.
