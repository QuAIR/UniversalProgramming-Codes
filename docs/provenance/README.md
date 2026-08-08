# Provenance records

`server-live-inventory.json` accounts for every file in the two remote trees
examined read-only on 2026-08-07. Each entry records a sanitized root-relative
path, byte count, source SHA-256, disposition, reason, and local target when one
exists. All 205 local snapshot hashes matched the live remote files.

Public labels are used throughout the inventory: the source trees are named
`qubit` and `general-d`, and the compute host is named `server`. These naming
changes do not alter the recorded hashes, sizes, or timestamps.

The original copies did not preserve filesystem metadata. After live access
was restored, the remote modification times were captured directly on
2026-08-08, normalized to UTC at one-second precision, and added to every
inventory entry. No local-copy timestamp was used as remote evidence.

The separate three-file `general-d-baseline-copy` is not a third source root;
it duplicates `general-d/kcopy_d2` and is excluded from the 57+148 count.
