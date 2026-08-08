# Experiment Code Repository Design

## Purpose

This repository collects the computational material supporting the universal
quantum programming project. It must provide a clear entry point for the
current implementations while preserving the provenance of diagnostic,
superseded, and unsuccessful experiments.

The migration draws from four sources:

1. the research-code tree removed from the manuscript repository after commit
   `4512790`;
2. files and result artifacts previously downloaded from server;
3. execution records that contain recoverable server-only diagnostic scripts;
   and
4. the current server working directory, when the server is reachable.

The public repository must never imply that a relaxation, failed run, or
uncertified numerical value is an exact result.

## Repository Layout

```text
UniversalProgramming-Codes/
|-- README.md
|-- src/
|   |-- matlab/
|   |   |-- common/
|   |   `-- kcopy_d2/
|   `-- python/
|-- experiments/
|   `-- server/
|       |-- README.md
|       |-- config/
|       |-- general_d/
|       `-- kcopy_d2/
|-- tests/
|   `-- matlab/
|-- results/
|   |-- summary.csv
|   |-- certified/
|   |-- logs/
|   `-- README.md
|-- figures/
|-- docs/
|   |-- experiment-manifest.md
|   |-- mathematical-reduction/
|   `-- development-notes/
`-- legacy/
    |-- README.md
    |-- failed-runs/
    |-- general-d-baseline/
    `-- linear-relaxation/
```

## Component Boundaries

### Shared source

`src/matlab/common/` contains reusable representation-theoretic routines:
the walled-Brauer construction, sector decomposition, algebra decomposition,
and Haar-random `SU(d)` helper. These files do not select an experiment or
contain server-specific paths.

`src/matlab/kcopy_d2/` contains the corrected row-space-reduced qubit solver.
Its public entry point is `gamma_k_d2_exact`. The default sample count remains
500, matching the reported runs. The solver saves the objective, positive and
negative weights, coefficient vectors, reduced block matrices, block
metadata, and residual diagnostics.

`src/python/` contains independent representation-dimension and symmetry
checks that do not require MATLAB.

### Server experiments

`experiments/server/` contains scripts that define actual server runs. The
general-dimension experiments and the qubit batches are separated. A small
configuration layer supplies the MATLAB, CVX, QETLAB, YALMIP, solver, output,
and log paths; committed scripts must not contain a personal home directory,
IP address, credential, or license path.

The qubit scripts retain distinct batches for `k=1,...,4` and `k=5,6`. The
latter remains an expensive batch and must not silently lower the sample
count. Launch scripts write a PID, a log, partial tables, and per-k result
files so that interrupted runs remain inspectable.

### Tests

MATLAB tests cover the inexpensive invariants that can be checked without
rerunning the large experiments:

- the `k=1` objective equals 5.5 within the solver tolerance;
- the known qubit programming-row ranks are reproduced for `k=1,...,4`;
- saved files contain `p1`, `p2`, coefficient vectors, block matrices, block
  metadata, and diagnostic information;
- repository paths resolve without relying on the former manuscript layout;
- the linear model is identified as a relaxation and is never called by the
  exact batch scripts.

Python figure and representation utilities receive lightweight command-line
smoke tests where their dependencies are available.

## Status and Provenance

Every experiment listed in `docs/experiment-manifest.md` has one of four
statuses:

- `validated`: solved and accompanied by the stated residual or certificate
  checks;
- `diagnostic`: useful for comparisons but not a reported optimum;
- `legacy`: superseded or known to contain a defect;
- `incomplete`: launched or partially assembled without a final validated
  result.

The manifest maps each experiment to its entry script, parameter set, solver,
result files, log, numerical status, and known limitations. It records the
original source commit or server path where available.

The old `m=0,1` qubit program belongs in `legacy/linear-relaxation/`. Its README
states explicitly that it is a lower-bound relaxation and is not equivalent
to the full k-copy SDP. The original general-dimension baseline with the
known subsystem-permutation defect belongs in
`legacy/general-d-baseline/`. Failed, under-sampled, and exploratory scripts
are retained under `legacy/failed-runs/` with short factual explanations. This
includes the temporary fixed-protocol cost check that completed for `k=1,2`
and encountered a MATLAB failure while attempting `k=3`.

## Results Policy

`results/summary.csv` is the machine-readable source for the numerical table.
It records `d`, `k`, objective value, status, method, solver, sample count,
certificate type, and source artifact.

`results/certified/` contains compact final `.mat` artifacts required for
independent analysis, including the qubit block-level solutions for `k=1` to
`4` and the certified general-dimension records. Partial or diagnostic binary
files are kept only when they provide information unavailable in a final
artifact, and their status is explicit in the manifest.

Logs are included only when they establish a result or explain a failed run.
Before publication they are sanitized to remove usernames, home paths, host
identifiers, CVX license details, and irrelevant startup output. Duplicate
archives, generated upload tarballs, caches, and reproducible PDFs are not
committed.

## Mathematical Documentation

`docs/mathematical-reduction/` contains the corrected reduction source and a
short guide connecting its constraints to the implementation. Statements
about exactness must distinguish the full polynomial row space from the
`m=0,1` relaxation. The documentation also states that the present row space
is generated numerically from 500 CPTP samples and checked on fresh channels;
it does not describe that numerical construction as a symbolic proof.

## Migration and Reconciliation

Files are first recovered from the last complete manuscript commit and
classified by the layout above. Known path breakage introduced by the former
`code/` to `research_code/core/` rename is corrected during migration.

When server is reachable, its `~/projects/kcopy_d2` tree is inventoried by
path, size, modification time, and checksum. Differences are copied into a
temporary local staging directory, reviewed, and then placed in the matching
repository component. Remote result files do not overwrite an existing
artifact unless their content and provenance are understood. If the server
remains unreachable, the repository is published from the recovered Git
objects and downloaded server artifacts, and the final report states that a
live remote reconciliation could not be completed.

The completed reconciliation followed that policy. Hashes and contents were
checked read-only on 2026-08-07. Because the first local copies lacked metadata,
modification times were subsequently read directly from the unchanged live
trees on 2026-08-08 and normalized to UTC in the inventory.

## Error Handling

Run scripts fail early when MATLAB, CVX, QETLAB, or the selected solver is
missing. They create output directories explicitly, save a partial result
after each completed `k`, and propagate the MATLAB exit status to the shell.
Configuration errors identify the missing path or dependency without
modifying source files.

Repository verification fails if it finds personal absolute paths, an exact
runner invoking the linear relaxation, missing manifest targets, MAT hash or
coverage mismatches, or a validated summary row backed only by diagnostic
evidence. The dependency-light Python verifier checks declared MAT schemas;
`tests/matlab/test_result_artifacts.m` loads the files and checks their actual
variables, retained values, and numerical acceptance inequalities.

## Publication

The migration is implemented on the existing `main` branch because the target
repository contains only its initial README and the user requested direct
synchronization. Before push, the complete diff, repository status, tests,
manifest links, and absence of sensitive paths are checked. No license is
invented; licensing remains unspecified until the repository owner chooses
one.

## Acceptance Criteria

The work is complete when:

1. every recovered experiment source file is either in a supported component
   or explicitly classified under `legacy/`;
2. the corrected qubit solver and its server batches have portable paths and
   preserve the 500-sample configuration;
3. validated result artifacts and block-level qubit data are present and
   referenced by the manifest;
4. reported values in `results/summary.csv` agree with the retained artifacts
   and manuscript table;
5. tests and static repository checks pass, or unavailable proprietary
   dependencies are reported precisely;
6. no credentials, private SSH data, personal paths, or unsanitized license
   output are committed; and
7. the resulting commit is pushed to `QuAIR/UniversalProgramming-Codes`.
