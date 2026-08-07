# Task 6 Report

Restored the local historical evidence package from source commit `4512790` without network access.

## Delivered inventory

- 34 non-partial MAT files: 13 certified (9 general-d and 4 exact d=2) and 21 diagnostic. The separate diagnostic `sk_invariance_output.txt` is text, not a 35th MAT.
- 15 compact sanitized support logs in `results/logs` and 2 failed/under-sampled logs in `legacy/failed-runs/logs`.
- The sparse strict-submultiplicativity TSV, mathematical reduction TeX, mathematical reference, historical d=3 and server-status snapshots, rerun/recovery plan, and Figure 3 CSV/script.

The four historical partial MAT/CSV artifacts were deliberately omitted. Also omitted: the reduction PDF, upload tarball, generated figures, caches, and crash dumps.

## MAT inspection

The configured Python lacks SciPy and h5py, so MATLAB `whos('-file', ...)` inspected all 34 retained MATs. Exact d=2 per-k records have `b1,b2,cost,info,p1,p2`; `info` carries solver and residual metadata but no saved block matrices. Full general-d records include coefficient, objective, status, dimension/sample, and certificate residual fields. Reduced-space/YALMIP records use `mineig,maxnh,tpres,fres`; older gamma/brute records only preserve their smaller historical schemas. Details are in `results/README.md`.

## Verification

- `python -m unittest tests.python.test_results_package -v`: passed with the optional figure-generation assertion skipped because Matplotlib is absent.
- `python -m unittest discover -s tests/python -q`: passed, 37 tests with 1 expected Matplotlib skip.
- `python tools/verify_repository.py`: scanned Task 6 files cleanly but returned the pre-existing Task 7 prerequisite failure `missing required file: docs/experiment-manifest.md`.
- `python -m py_compile figures/make_fig3_kcopy_decay.py tests/python/test_results_package.py`: passed.
- Sensitive-path and partial-output scans: clean.

The figure script uses portable `tempfile`/`MPLCONFIGDIR` handling and writes only under `figures/generated` (or `FIGURES_OUTPUT_DIR`). It was not run to completion because the configured runtime has no Matplotlib.
