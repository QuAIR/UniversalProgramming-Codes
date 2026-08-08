# Strict Submultiplicativity Case Implementation Plan

> **Scope update:** The user reduced the requested publication package to a
> compact GitHub example. The final implementation keeps one verification
> function, one runner, one lightweight structural test, and linked README
> material. The full CVX norm recomputation is optional and is not a release
> gate.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restore the historical finite-qubit strict-submultiplicativity example as a supported MATLAB experiment with exact structural certificate checks, a solver-backed numerical norm comparison, tests, and reader-facing documentation.

**Architecture:** An experiment-local loader reconstructs the historical sparse rational correction matrix. A single verification API first performs dependency-free structural checks and optionally invokes two CVX SDPs: one for the optimal one-copy processor and one for the fixed correlated processor. A short runner, fast structural test, optional solver smoke test, and linked documentation expose the example without changing the universal k-copy solver.

**Tech Stack:** MATLAB, CVX with an SDP solver supported by CVX, Git, Python `unittest` for static repository checks. QETLAB and YALMIP are not required for this case.

## Global Constraints

- Treat `results/certified/strict_submult_C_sparse.tsv` as exact rational correction data, not as a complete primal-dual rational certificate of the strict norm inequality.
- Describe the result as a "reproducible numerical strict-submultiplicativity example".
- Use register order `S1,S2,A1,A2,B1,B2,S1_out,S2_out` for the `256 x 256` correction Choi matrix.
- Structural mode must run without CVX, QETLAB, or YALMIP.
- Full mode may require only MATLAB, CVX, and the configured CVX solver.
- Keep generated outputs below `results/generated/`; do not modify the historical TSV.
- Use ASCII in new source and documentation files.

---

### Task 1: Certificate Loader And Structural Verification

**Files:**
- Create: `experiments/strict_submultiplicativity/load_strict_submult_certificate.m`
- Create: `experiments/strict_submultiplicativity/verify_strict_submultiplicativity.m`
- Create: `tests/matlab/test_strict_submultiplicativity_certificate.m`
- Modify: `tests/matlab/test_paths.m`

**Interfaces:**
- Produces: `[JCorrection, meta] = load_strict_submult_certificate(certificatePath)`, where `JCorrection` is `256 x 256` and `meta` contains `dimension`, `entryCount`, `registerOrder`, and `certificatePath`.
- Produces: `report = verify_strict_submultiplicativity(opts)`, where structural mode is selected by `opts.solve = false` and returns the fields named below.
- Consumes: `results/certified/strict_submult_C_sparse.tsv` with columns `row`, `col`, `numerator`, and `denominator`.

- [ ] **Step 1: Add a failing MATLAB structural test**

Create `tests/matlab/test_strict_submultiplicativity_certificate.m` with these assertions:

```matlab
clear; clc;
repoRoot = fileparts(fileparts(fileparts(mfilename('fullpath'))));
caseRoot = fullfile(repoRoot, 'experiments', 'strict_submultiplicativity');
addpath(caseRoot);

opts = struct('solve', false, 'verbose', false);
report = verify_strict_submultiplicativity(opts);

assert(strcmp(report.mode, 'structural'));
assert(report.certificateNnz == 360);
assert(isequal(report.registerOrder, ...
    {'S1','S2','A1','A2','B1','B2','S1_out','S2_out'}));
assert(max(report.channelTpResiduals) < 1e-13);
assert(report.correctionHermiticityResidual < 1e-13);
assert(report.correctionOutputTraceResidual < 1e-13);
assert(all(size(report.annihilationResiduals) == [2, 2]));
assert(max(report.annihilationResiduals, [], 'all') < 1e-13);
assert(isnan(report.oneCopyCost));
assert(~report.isStrictNumerical);

fprintf('TEST_STRICT_SUBMULT_CERTIFICATE_OK nnz=%d residual=%.3e\n', ...
    report.certificateNnz, max(report.annihilationResiduals, [], 'all'));
```

Add `verify_strict_submultiplicativity` and
`load_strict_submult_certificate` to the in-repository resolution assertions
in `tests/matlab/test_paths.m` after adding the experiment directory to the
MATLAB path.

- [ ] **Step 2: Run the structural test and verify the expected failure**

Run:

```powershell
matlab -batch "run('tests/matlab/test_strict_submultiplicativity_certificate.m')"
```

Expected: failure because `verify_strict_submultiplicativity` is undefined.

- [ ] **Step 3: Implement the validated TSV loader**

Implement `load_strict_submult_certificate.m` with this contract:

```matlab
function [JCorrection, meta] = load_strict_submult_certificate(certificatePath)
%LOAD_STRICT_SUBMULT_CERTIFICATE Reconstruct the historical rational J_C.
```

Use `detectImportOptions` and `readtable` with tab delimiter. Require the exact
column names `row`, `col`, `numerator`, `denominator`; 360 rows; integer indices
in `[1,256]`; nonzero denominators; unique `(row,col)` pairs; finite, nonzero
rational values; and a Hermitian reconstructed matrix. Build with
`sparse(row,col,double(numerator)./double(denominator),256,256)` and return
`full(...)`. Raise named errors beginning with
`load_strict_submult_certificate:` for missing files, schema failures, and
invalid entries.

Set metadata exactly as follows:

```matlab
meta.dimension = 256;
meta.entryCount = 360;
meta.registerOrder = ...
    {'S1','S2','A1','A2','B1','B2','S1_out','S2_out'};
meta.certificatePath = certificatePath;
```

- [ ] **Step 4: Implement structural mode of the verification API**

Implement `verify_strict_submultiplicativity.m` with defaults:

```matlab
defaults.solve = false;
defaults.verbose = true;
defaults.solver = 'sdpt3';
defaults.cvxRoot = getenv('UP_CVX_ROOT');
defaults.certificatePath = fullfile(repoRoot, 'results', 'certified', ...
    'strict_submult_C_sparse.tsv');
defaults.residualTolerance = 1e-10;
defaults.gapTolerance = 1e-6;
defaults.saveResult = false;
defaults.resultPath = fullfile(repoRoot, 'results', 'generated', ...
    'strict_submultiplicativity.mat');
```

Construct each channel from the three Kraus operators and form

```matlab
JChannel = sum_r vec(K_r) * vec(K_r)';
program = JChannel / 2;
```

where `vec(K_r) = K_r(:)` uses MATLAB column-major order. Implement local
helpers:

```matlab
function A = local_induced_choi_map(program, signalDim, outputDim)
function T = local_output_trace_map(inputDim, outputDim)
function Y = local_permute_operator(X, dims, permutation)
```

`local_induced_choi_map` returns the sparse matrix satisfying
`vec(J_induced) = A * vec(J_map)`. `local_output_trace_map` returns the sparse
matrix satisfying `vec(Tr_output(J_map)) = T * vec(J_map)`. These maps avoid
toolbox partial-trace functions and work with later CVX vector expressions.

For a product program, permute `kron(program_i,program_j)` from
`A1,B1,A2,B2` to `A1,A2,B1,B2` using permutation `[1,3,2,4]`. Check

```matlab
Aij * JCorrection(:) == 0
```

for all four pairs. Check the output trace with signal-program input dimension
64 and output dimension 4.

Return a scalar structure with at least:

```matlab
report.mode = 'structural';
report.registerOrder = meta.registerOrder;
report.certificateNnz = nnz(JCorrection);
report.channelTpResiduals = channelTpResiduals;
report.correctionHermiticityResidual = norm(JCorrection-JCorrection','fro');
report.correctionOutputTraceResidual = norm(T * JCorrection(:));
report.annihilationResiduals = annihilationResiduals;
report.maxAnnihilationResidual = max(annihilationResiduals,[],'all');
report.oneCopyCost = NaN;
report.productCost = NaN;
report.correlatedCost = NaN;
report.strictGap = NaN;
report.oneCopyStatus = 'not_run';
report.correlatedStatus = 'not_run';
report.isStrictNumerical = false;
```

Raise `verify_strict_submultiplicativity:structuralResidual` if a structural
residual exceeds `opts.residualTolerance`.

- [ ] **Step 5: Run the structural tests and verify they pass**

Run:

```powershell
matlab -batch "run('tests/matlab/test_strict_submultiplicativity_certificate.m'); run('tests/matlab/test_paths.m')"
```

Expected: both scripts print their `*_OK` markers and MATLAB exits zero.

- [ ] **Step 6: Commit the structural implementation**

```powershell
git add experiments/strict_submultiplicativity/load_strict_submult_certificate.m experiments/strict_submultiplicativity/verify_strict_submultiplicativity.m tests/matlab/test_strict_submultiplicativity_certificate.m tests/matlab/test_paths.m
git commit -m "Add strict submultiplicativity certificate checks"
```

---

### Task 2: Solver-Backed Numerical Reproduction

**Files:**
- Modify: `experiments/strict_submultiplicativity/verify_strict_submultiplicativity.m`
- Create: `experiments/strict_submultiplicativity/run_strict_submultiplicativity.m`
- Create: `tests/matlab/smoke_strict_submultiplicativity.m`

**Interfaces:**
- Consumes: structural report and channel/program Choi matrices produced inside `verify_strict_submultiplicativity`.
- Produces: full-mode report fields `oneCopyCost`, `productCost`, `correlatedCost`, `strictGap`, `oneCopyStatus`, `correlatedStatus`, `oneCopyTpResidual`, `correlatedTpResidual`, `correlatedProgrammingResiduals`, and `isStrictNumerical`.
- Produces: `run_strict_submultiplicativity.m` as the documented full-mode entry point.

- [ ] **Step 1: Add a solver-backed smoke test before full-mode code**

Create `tests/matlab/smoke_strict_submultiplicativity.m`:

```matlab
clear; clc;
repoRoot = fileparts(fileparts(fileparts(mfilename('fullpath'))));
addpath(fullfile(repoRoot, 'experiments', 'strict_submultiplicativity'));
addpath(fullfile(repoRoot, 'src', 'matlab'));
cfg = up_config();

opts = struct('solve', true, 'verbose', true, 'solver', cfg.solver, ...
    'cvxRoot', cfg.cvxRoot, 'saveResult', false);
report = verify_strict_submultiplicativity(opts);

assert(contains(lower(report.oneCopyStatus), 'solved'));
assert(contains(lower(report.correlatedStatus), 'solved'));
assert(report.oneCopyTpResidual < 1e-6);
assert(report.correlatedTpResidual < 1e-6);
assert(max(report.correlatedProgrammingResiduals, [], 'all') < 1e-6);
assert(report.strictGap > report.gapTolerance);
assert(report.isStrictNumerical);

fprintf('SMOKE_STRICT_SUBMULT_OK one=%.12f joint=%.12f gap=%.3e\n', ...
    report.oneCopyCost, report.correlatedCost, report.strictGap);
```

- [ ] **Step 2: Run the smoke test and verify the expected full-mode failure**

Run:

```powershell
matlab -batch "run('tests/matlab/smoke_strict_submultiplicativity.m')"
```

Expected: failure because full solver mode is not implemented and leaves
`oneCopyStatus` equal to `not_run`.

- [ ] **Step 3: Implement the one-copy processor SDP**

When `opts.solve` is true, add `opts.cvxRoot` recursively and run `cvx_setup`
only if `cvx_begin` is unavailable. Raise
`verify_strict_submultiplicativity:missingCVX` if CVX remains unavailable.

For input order `S,A,B` and output `S_out`, define `16 x 16` Hermitian
variables `JPlus` and `JMinus`, scalar variables `pPlus,pMinus`, and
`JOne = JPlus-JMinus`. Minimize `pPlus+pMinus` subject to:

```matlab
JPlus >= 0;
JMinus >= 0;
TOne * JPlus(:) == pPlus * reshape(eye(8), [], 1);
TOne * JMinus(:) == pMinus * reshape(eye(8), [], 1);
AOne{i} * JOne(:) == JChannels{i}(:), i = 1,2;
```

Use `cvx_precision high` and `cvx_solver(opts.solver)`. Reject statuses that do
not contain `Solved`, case-insensitively. Record the optimal matrix and compute
the TP and programming residuals after `cvx_end`.

- [ ] **Step 4: Form the correlated processor in certificate order**

Form `kron(JOne,JOne)` in order
`S1,A1,B1,S1_out,S2,A2,B2,S2_out`, then use
`local_permute_operator` with permutation `[1,5,2,6,3,7,4,8]` to obtain

```text
S1,S2,A1,A2,B1,B2,S1_out,S2_out.
```

Set `JProduct` to the permuted matrix and `JHat = JProduct + JCorrection`.
Construct four joint target Choi matrices by permuting
`kron(JChannel_i,JChannel_j)` from `S1,S1_out,S2,S2_out` to
`S1,S2,S1_out,S2_out` using `[1,3,2,4]`. Verify the four joint programming
residuals from the precomputed induced-Choi maps.

- [ ] **Step 5: Implement the fixed-map correlated cost SDP**

Define `256 x 256` Hermitian semidefinite variables `JHatPlus,JHatMinus` and
scalars `qPlus,qMinus`. Minimize `qPlus+qMinus` subject to:

```matlab
JHatPlus - JHatMinus == JHat;
THat * JHatPlus(:) == qPlus * reshape(eye(64), [], 1);
THat * JHatMinus(:) == qMinus * reshape(eye(64), [], 1);
```

Set

```matlab
report.oneCopyCost = pPlus + pMinus;
report.productCost = report.oneCopyCost^2;
report.correlatedCost = qPlus + qMinus;
report.strictGap = report.productCost - report.correlatedCost;
report.gapTolerance = opts.gapTolerance;
report.isStrictNumerical = report.strictGap > opts.gapTolerance;
```

Raise `verify_strict_submultiplicativity:numericalResidual` for TP or
programming residuals above `1e-6`, and
`verify_strict_submultiplicativity:noStrictGap` when the gap does not exceed
`opts.gapTolerance`.

If `opts.saveResult` is true, create the parent directory of
`opts.resultPath` and save only `report`; do not duplicate the historical TSV
or save CVX internals.

- [ ] **Step 6: Implement the reader-facing runner**

Create `run_strict_submultiplicativity.m`:

```matlab
clear; clc;
caseRoot = fileparts(mfilename('fullpath'));
repoRoot = fileparts(fileparts(caseRoot));
addpath(caseRoot);
addpath(fullfile(repoRoot, 'src', 'matlab'));
cfg = up_config();

opts = struct('solve', true, 'verbose', true, 'solver', cfg.solver, ...
    'cvxRoot', cfg.cvxRoot, 'saveResult', true, ...
    'resultPath', fullfile(cfg.resultsRoot, ...
        'strict_submultiplicativity.mat'));
report = verify_strict_submultiplicativity(opts); %#ok<NASGU>
```

- [ ] **Step 7: Run fast and full MATLAB verification**

Run:

```powershell
matlab -batch "run('tests/matlab/test_strict_submultiplicativity_certificate.m')"
matlab -batch "run('tests/matlab/smoke_strict_submultiplicativity.m')"
```

Expected: the structural marker and `SMOKE_STRICT_SUBMULT_OK` print, both
solvers report a solved status, and the printed gap is positive above `1e-6`.

- [ ] **Step 8: Commit the solver-backed reproduction**

```powershell
git add experiments/strict_submultiplicativity/verify_strict_submultiplicativity.m experiments/strict_submultiplicativity/run_strict_submultiplicativity.m tests/matlab/smoke_strict_submultiplicativity.m
git commit -m "Reproduce strict submultiplicativity numerically"
```

---

### Task 3: Reader Documentation And Repository Integration

**Files:**
- Create: `experiments/strict_submultiplicativity/README.md`
- Modify: `README.md`
- Modify: `docs/experiment-manifest.md`
- Modify: `results/certified/README.md`
- Modify: `tests/python/test_repository.py`

**Interfaces:**
- Consumes: the final command, report fields, actual numerical values, and evidence boundary from Tasks 1 and 2.
- Produces: linked navigation from the root README, experiment manifest, and certificate inventory to the independent case README.

- [ ] **Step 1: Add failing static documentation assertions**

Add a test method to `tests/python/test_repository.py` that reads the four
documentation files and asserts:

```python
case_readme = ROOT / "experiments" / "strict_submultiplicativity" / "README.md"
self.assertTrue(case_readme.is_file())
text = case_readme.read_text(encoding="utf-8")
self.assertIn("reproducible numerical strict-submultiplicativity example", text)
self.assertIn("S1,S2,A1,A2,B1,B2,S1_out,S2_out", text)
self.assertIn("run_strict_submultiplicativity.m", text)
self.assertIn("not a complete primal-dual rational certificate", text)
for path in [ROOT / "README.md", ROOT / "docs" / "experiment-manifest.md",
             ROOT / "results" / "certified" / "README.md"]:
    self.assertIn("strict_submultiplicativity", path.read_text(encoding="utf-8"))
```

- [ ] **Step 2: Run the static test and verify the expected failure**

Run:

```powershell
python -m unittest tests.python.test_repository
```

Expected: failure because the case README and navigation links do not exist.

- [ ] **Step 3: Write the independent case README**

Document:

- the two Kraus families and parameter triples;
- normalized program convention `pi_E = J_E/2`;
- the certificate register order and 360-entry TSV schema;
- structural mode command and the exact checks it performs;
- full mode command, MATLAB/CVX dependency, environment variables, report
  fields, and generated MAT location;
- the actual one-copy cost, correlated cost, and positive gap printed by the
  successful Task 2 smoke run;
- the distinction between exact rational matrix-data checks and numerical SDP
  evidence;
- the historical Overleaf provenance commits `b73a1de`, `e1af873`, and
  `dc58b12`.

Use the required phrase and disclaimer verbatim:

```text
This is a reproducible numerical strict-submultiplicativity example.
The sparse correction data is not a complete primal-dual rational certificate
of the strict norm inequality.
```

- [ ] **Step 4: Add repository navigation and manifest entry**

Add the case directory to the root repository-layout table and add a short
"Strict submultiplicativity example" section after the quick start. Add an
experiment-manifest entry with status `validated structural certificate data;
numerical strict-gap reproduction`, its entry point, dependencies, source TSV,
checks, output, and limitations. Replace the one-line certificate description
in `results/certified/README.md` with a link to the case README and the evidence
boundary.

- [ ] **Step 5: Run documentation and repository checks**

Run:

```powershell
python -m unittest tests.python.test_repository
python tools/verify_repository.py
```

Expected: both commands exit zero.

- [ ] **Step 6: Commit the documentation integration**

```powershell
git add experiments/strict_submultiplicativity/README.md README.md docs/experiment-manifest.md results/certified/README.md tests/python/test_repository.py
git commit -m "Document strict submultiplicativity example"
```

---

### Task 4: Final Verification And Publication

**Files:**
- Verify: all files created or modified in Tasks 1-3

**Interfaces:**
- Consumes: all implementation, tests, and documentation.
- Produces: a clean, pushed `main` branch containing the independent case.

- [ ] **Step 1: Run the complete dependency-light suite**

```powershell
python -m unittest discover -s tests/python -p "test_*.py"
python tools/verify_repository.py
```

Expected: all tests pass and the verifier exits zero.

- [ ] **Step 2: Run MATLAB structural regression tests**

```powershell
matlab -batch "run('tests/matlab/test_paths.m'); run('tests/matlab/test_strict_submultiplicativity_certificate.m'); run('tests/matlab/test_portable_configuration.m')"
```

Expected: all three scripts print their success markers and MATLAB exits zero.

- [ ] **Step 3: Run the full solver-backed smoke test once more**

```powershell
matlab -batch "run('tests/matlab/smoke_strict_submultiplicativity.m')"
```

Expected: solved statuses, residuals below `1e-6`, and a strict gap above
`1e-6`.

- [ ] **Step 4: Inspect the final change set**

```powershell
git diff --check origin/main...HEAD
git status --short --branch
git diff --stat origin/main...HEAD
```

Expected: no whitespace errors, no untracked generated result, and only the
planned case, tests, design/plan, and documentation changes.

- [ ] **Step 5: Commit any final plan-status update and push**

```powershell
git add docs/superpowers/plans/2026-08-08-strict-submultiplicativity-case.md
git commit -m "Complete strict submultiplicativity case plan"
git fetch origin
git push origin main
```

Expected: `main` advances on `origin` with no non-fast-forward error.
