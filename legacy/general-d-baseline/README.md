# Defective General-D Baseline

`gamma_k.m` and its adjacent `decompose_brauer_algebra.m` are historical copies
of the former general-d baseline. The `PermuteSystems` convention in
`gamma_k.m` is known defective for k>=3. This is not a supported entry point;
it is retained only so old generated programs and output records can be read.

The `generators/` scripts are historical-but-ported wrappers, not
byte-identical copies of `gamma_k.m`. In particular, `gen.sh` intentionally
preserves the historical transformation pipeline: it changes the decomposition
method, replaces the permutation convention, reduces equality families, and
symmetrizes PSD constraints. Generated scripts are legacy and unsupported.
The portability patch supplies repository-root and `UP_QETLAB_ROOT`
configuration through `up_config`; `UP_REPO_ROOT` remains an override for a
generated script, which otherwise uses the repository root embedded when it
was generated. Generated MAT files are saved under the configured local
results root.

`genbrute.sh` requires the historical `brute.m` input, which is absent from
commit 4512790 and is therefore not supplied here; it fails explicitly until
that provenance input is recovered.

`docs/provenance/legacy-task-5-manifest.json` records local byte hashes, source
blob identifiers, and execution-record references. It is a provenance record,
not self-contained proof of an external source repository or server execution.

The sample defaults in the generators remain historical: S defaults to 500 and
the seed defaults to 0. Generated outputs belong under the local results root.
