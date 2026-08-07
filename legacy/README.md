# Legacy Experiment Archive

This directory preserves superseded, defective, incomplete, and under-sampled
experiment implementations for provenance only. Nothing in `src/` or
`experiments/` imports or calls code from this directory.

Do not use `general-d-baseline/gamma_k.m` as a supported entry point. Its
historical `PermuteSystems` convention is defective for k>=3. The qubit
prototype's full raw-row mode is distinct from its m=0,1 linear mode. The
linear mode is a lower bound, not equivalent to the exact SDP, can lie below the exact optimum, and must not be cited as gamma_k.

Each retained runner resolves paths and outputs locally, but these warnings
remain intentional: archived scripts are not supported computational results.
