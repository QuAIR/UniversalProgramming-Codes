# UniversalProgramming-Codes

Computational material for universal programming of general quantum channels.

The supported qubit solver is `src/matlab/kcopy_d2/gamma_k_d2_exact.m`; server
batch entry points are under `experiments/quair06`. Curated numerical evidence
and its machine-readable hash manifest are under `results`. Superseded,
defective, exploratory, and server-only historical sources are clearly marked
under `legacy`.

The quair06 trees were reconciled read-only on 2026-08-07: 57 files from the
qubit project and 148 from the general-d project, with no SHA-256 mismatches.
The per-file disposition is recorded in
`docs/provenance/quair06-live-inventory.json`. No remote job was run or changed
as part of that reconciliation.

The additional saved-block d=2,k=5 artifact is retained only as a diagnostic
numerical candidate. Its sampled and 50-fresh-channel residual checks pass,
but it is not a rigorous all-CPTP feasibility certificate or an optimum; the
canonical summary value is unchanged. The corresponding k=6 checkpoint is
incomplete.
