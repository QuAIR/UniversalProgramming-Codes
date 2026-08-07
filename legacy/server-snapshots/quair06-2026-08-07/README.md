# quair06 snapshot (2026-08-07)

This directory preserves remote-only source files from the read-only live
reconciliation on 2026-08-07. It is a historical snapshot, not a supported
entry point. Portable and supported counterparts are referenced directly by
`docs/provenance/quair06-live-inventory.json` and are not duplicated here.

The archived MATLAB scripts include exploratory, generated, under-sampled,
and known-defective variants. In particular, the old general-dimension
baseline inherits the subsystem-permutation issue documented in
`legacy/general-d-baseline/README.md`, and the qubit linear scripts are a
relaxation rather than the exact k-copy SDP. Hard-coded server paths were
replaced by neutral placeholders; no mathematical expression was changed.

The `pqga/pbt_bound` scripts are retained because they were present only in
the live tree. Their description of a certified bound is a recovered claim,
not independently re-proven in this reconciliation. The only code change is
the local import path in `make_fig3.py`, which now resolves `pbt_bound.py`
from the same directory.

No remote job was running when the tree was checked, and this reconciliation
did not start, stop, or modify any remote job or file.
