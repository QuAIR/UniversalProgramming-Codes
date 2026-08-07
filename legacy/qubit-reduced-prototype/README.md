# Qubit Reduced Prototype

This directory is a superseded historical prototype, retained for provenance
only. `gamma_k_d2.m` has two distinct modes: a full raw-row mode and an m=0,1
mode. Only the m=0,1 mode is the linear relaxation.

The linear relaxation is a lower bound, not equivalent to the exact SDP, can lie below the exact optimum, and must not be cited as gamma_k. In particular,
the full raw-row mode and the m=0,1 linear relaxation are not interchangeable.
The local driver retains its historical `opts.certFresh = 20`, so its fresh
channel checking is under-sampled relative to the supported solver's 50-sample
check. These runners are archived provenance, not supported experiments.
