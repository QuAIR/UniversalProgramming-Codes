# quair06 rerun plan for updated kcopy_d2

This plan matches the updated proof split in `../kcopy_d2_reduction.tex`.

## Current mathematical interpretation

- `gamma_k_d2(k, 'full')` is the exact all-row SDP.
- `gamma_k_d2(k, 'linear')` keeps only the `m=0,1` rows and is a lower-bound
  relaxation.
- The reported quantity

```text
gap = gamma_full - gamma_linear
```

is diagnostic.  A positive gap means the omitted `m>=2` rows are binding.

## Server run

Use quair06:

```bash
cd ~/projects/kcopy_d2
./launch_quair06_k14.sh
```

The launcher writes:

```text
logs/kcopy_d2_updated_k14.nohup
logs/kcopy_d2_updated_k14.pid
logs/kcopy_d2_updated_k14.log
kcopy_d2_quair06_updated_k14_partial.mat
kcopy_d2_quair06_updated_k14.csv
kcopy_d2_quair06_updated_k14.mat
```

## Caveat

The SDP variables are Schur-Weyl reduced, but the current MATLAB code still
assembles redundant polarized rows by forming full `4^(k+1)` matrices.  Thus
`k=4` can be assembly-bound even though the updated proof identifies a much
smaller multiplicity-resolved row system.
