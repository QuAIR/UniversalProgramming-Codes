# quair06 Reconciliation Plan

Live reconciliation is deliberately deferred: this migration has no server or network access, and the restored package is a historical snapshot rather than a fresh validation.

For exact d=2 k=5,6, recover only through `experiments/quair06/kcopy_d2/run_exact_k56.m` after checking its SHA-256: `49D83FEEBFA18F1674CF634CE0FA2EE8312DCD848430150CDA5E68E9A4A8DC70`. The matching wrapper checksum is `791E6150E389A09C7AD1E71A1B8C930F61AA1CC70C85F909C8940B88CCCC096E`. Use `Get-FileHash -Algorithm SHA256` before recovery, configure local CVX and QETLAB paths, preserve `opts.s=500` and `opts.certFresh=50`, and retain only final non-partial per-k MATs after independent review. The source backup has no final exact k=5 or k=6 MAT, so this document supplies recovery steps, not results.
