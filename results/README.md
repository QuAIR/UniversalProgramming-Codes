# Historical Result Evidence

This directory restores curated evidence from source commit `4512790`; it does not report a new run. Values in `summary.csv` are universal-processor programming costs (overheads), not unitary-inversion fidelities.

## Inventory and classification

All 34 non-partial MAT files in the historical `research_code/results` backup are retained. The nine validated general-d records are in `certified/general_d`, and the four final exact d=2 per-k records are in `certified/kcopy_d2`. The other 21 records are diagnostic, with collision-safe `historical_*` filenames. The four `*_partial.mat` and `*_partial.csv` files are deliberately excluded: they are resumable, ephemeral outputs forbidden by repository policy. No tarball, cache, crash dump, generated figure, or generated reduction PDF is retained.

## MAT schemas

MATLAB `whos('-file', ...)` inspected every retained MAT. The exact d=2 files have `b1, b2, cost, info, p1, p2`; `info` contains objective, solver status/time, sample count, row counts, basis/block widths, and residuals. It does not contain saved block matrices. The historical aggregate exact file has a T table and opts struct; the historical linear aggregate has vectors, status strings, and diagnostic solver information.

The full general-d certificates have `cost, d, k, s, cvx_status`, coefficients `b1,b2`, `p1,p2`, eigenvalue/Hermiticity/TP fields, and `fres`. Structured records use the same core fields; reduced-space and YALMIP records instead record `mineig`, `maxnh`, `tpres`, and `fres`. Older gamma and brute records only retain `cost, d, k, s, cvx_status` (and often `method`), so they are not certificates.

The d=2,k=1 formula also has a retained exact d=2 SDP MAT, so that row links to `certified/kcopy_d2/exact_d2_k1.mat`; it remains an analytic value. The other k=1 rows have no historical per-row MAT, so their artifacts are intentionally blank. The d=2,k=2 row uses the retained exact d=2 MAT while its certificate text records the independent Hilbert and brute checks. The d=3,k=2 row points to the 800-sample diagnostic MAT and is supported by its fixed and 500-sample repeats. The d=3,k=4 row points to the retained YALMIP log, with a separate CVX cross-check; it is diagnostic because there is no full-space certificate.

`logs/` contains compact sanitized numerical evidence. `legacy/failed-runs/logs` retains the under-sampled and unbounded records needed to explain exclusions.
