# Provenance records

`quair06-live-inventory.json` accounts for every file in the two remote trees
examined read-only on 2026-08-07. Each entry records a sanitized root-relative
path, byte count, source SHA-256, disposition, reason, and local target when one
exists. All 205 local snapshot hashes matched the live remote files.

Remote modification times are not recorded. The snapshots were copied without
metadata preservation, so their local timestamps are not evidence of remote
mtime. The inventory marks this field unavailable rather than substituting the
local timestamp.

The separate three-file `pqga-baseline` copy is not a third source root; it
duplicates `pqga-full/kcopy_d2` and is excluded from the 57+148 count.
