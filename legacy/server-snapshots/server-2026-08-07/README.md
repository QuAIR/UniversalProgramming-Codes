# Server Snapshot (2026-08-07)

This directory preserves remote-only source files from the read-only live
reconciliation on 2026-08-07. It is a historical snapshot, not a supported
entry point. Portable and supported counterparts are referenced directly by
`docs/provenance/server-live-inventory.json` and are not duplicated here.

The archived MATLAB scripts include exploratory, generated, under-sampled,
and known-defective variants. In particular, the old general-dimension
baseline inherits the subsystem-permutation issue documented in
`legacy/general-d-baseline/README.md`, and the qubit linear scripts are a
relaxation rather than the exact k-copy SDP. Files with no required change are
byte-identical to the read-only source snapshot. In the remaining files,
hard-coded server paths were replaced by neutral placeholders. Seven generated
`gamma_run_*.m` files also had trailing whitespace removed so that repository
whitespace checks remain clean. These transformations are recorded per file in
`docs/provenance/server-live-inventory.json`; no mathematical expression was
changed.

The `general-d/pbt_bound` scripts are retained because they were present only in
the live tree. Their description of a certified bound is a recovered claim,
not independently re-proven in this reconciliation. The only code change is
the local import path in `make_fig3.py`, which now resolves `pbt_bound.py`
from the same directory.

No remote job was running when the tree was checked, and this reconciliation
did not start, stop, or modify any remote job or file.
