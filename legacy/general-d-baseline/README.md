# Defective General-D Baseline

`gamma_k.m` and its adjacent `decompose_brauer_algebra.m` are historical copies
of the former general-d baseline. The `PermuteSystems` convention in
`gamma_k.m` is known defective for k>=3. This is not a supported entry point;
it is retained only so old generated programs and output records can be read.

The `generators/` scripts preserve the historical generation pipeline without
changing its generated mathematical assembly. `gen.sh` now obtains QETLAB via
the portable `UP_QETLAB_ROOT` configuration path. `genbrute.sh` requires the
historical `brute.m` input, which is absent from commit 4512790 and is therefore
not supplied here; it fails explicitly until that provenance input is recovered.

The sample defaults in the generators remain historical: S defaults to 500 and
the seed defaults to 0. Generated outputs belong under the local results root.
