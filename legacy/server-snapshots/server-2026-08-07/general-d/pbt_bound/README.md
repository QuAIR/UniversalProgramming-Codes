# Historical PBT bound scripts

These two scripts were recovered from the live server tree on 2026-08-07.
They are diagnostic historical code, not a supported result pipeline.

The scripts describe their finite-k PBT expression as certified. That wording
is part of the recovered claim and was not independently re-proven during this
code reconciliation. In particular, this archive does not establish the
mathematical converse or the interpretation of the plotted sampled SDP values.

`make_fig3.py` was changed only so that it imports `pbt_bound.py` from this
directory. No formula or numerical data was changed.
