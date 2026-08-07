# Failed and Under-Sampled Runs

This directory retains failed and under-sampled runs for provenance only. It
does not provide supported experiment entry points or reportable optima.

`fixed_protocol_cost_check.m` is recovered from a recorded server-only
diagnostic. Its historical loop remains k=1:3 with SDPT3, but it must not be
used for a new k=3 solve in this migration. The recorded outcomes are exactly:

```text
k=1: 5.500000001339, Solved
k=2: 3.666666669558, Solved
k=3: MATLAB terminated during the attempted run
```

No k=3 cost is claimed. The diagnostic and other failed or under-sampled
artifacts are retained only for provenance.
