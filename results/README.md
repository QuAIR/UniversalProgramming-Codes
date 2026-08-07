# Historical Result Evidence

This directory restores curated evidence from source commit `4512790`; it does not report a new run. Values in `summary.csv` are universal-processor programming costs (overheads), not unitary-inversion fidelities.

## Inventory and classification

All 34 non-partial MAT files in the historical `research_code/results` backup are retained. The nine validated general-d records are in `certified/general_d`, and the four final exact d=2 per-k records are in `certified/kcopy_d2`. The other 21 records are diagnostic, with collision-safe `historical_*` filenames. The four `*_partial.mat` and `*_partial.csv` files are deliberately excluded: they are resumable, ephemeral outputs forbidden by repository policy. No tarball, cache, crash dump, generated figure, or generated reduction PDF is retained.

`mat-artifacts.json` is the machine-readable inventory. For every retained MAT it records the current SHA-256, source-commit path and hash, variable names, classification, and available numerical/status/residual fields. Certified entries additionally contain scalar checks consumed by the MATLAB loader test.

## MAT schemas

MATLAB `whos('-file', ...)` inspected every retained MAT. The exact d=2 files have `b1, b2, cost, info, p1, p2`; `info` contains objective, solver status/time, sample count, row counts, basis/block widths, and residuals. It does not contain saved block matrices. The historical aggregate exact file has a T table and opts struct; the historical linear aggregate has vectors, status strings, and diagnostic solver information.

The full general-d certificates have `cost, d, k, s, cvx_status`, coefficients `b1,b2`, `p1,p2`, eigenvalue/Hermiticity/TP fields, and `fres`. Structured records use the same core fields; reduced-space and YALMIP records instead record `mineig`, `maxnh`, `tpres`, and `fres`. Older gamma and brute records only retain `cost, d, k, s, cvx_status` (and often `method`), so they are not certificates.

The d=2,k=1 formula also has a retained exact d=2 SDP MAT, so that row links to `certified/kcopy_d2/exact_d2_k1.mat`; it remains an analytic value. The other k=1 rows have no historical per-row MAT, so their artifacts are intentionally blank. The d=2,k=2 row uses the retained exact d=2 MAT while its certificate text records the independent Hilbert checks and the brute-force evidence in `results/logs/brute_d2_k2.log`. The d=3,k=2 row points to the 800-sample diagnostic MAT and is supported by its fixed and 500-sample repeats. The d=3,k=4 objective and status were printed before both historical wrappers exited with code 143, but neither completed its certificate stage. Those logs are therefore classified as post-solve terminations under `legacy/failed-runs/logs`; the summary remains diagnostic.

The aggregate exact d=2 MAT was copied from source commit `4512790` and differs only in four `opts` path strings, which were replaced by neutral placeholders. The source file and source-commit Git blob agree, but their actual SHA-256 is `7c6a54ad675fe91986516cebe9edb37f0023250e19052eecb8df0cab3dff2002`, not the previously reported `7c6a54ad675fe91986516cebe9edb37f0023250e19052eecb8df0f6241ae3e3`. The exact fields and both hashes are recorded in `mat-artifacts.json`.

`logs/` contains compact sanitized numerical evidence. `legacy/failed-runs/logs` retains under-sampled, unbounded, and post-solve-terminated records needed to explain exclusions.
