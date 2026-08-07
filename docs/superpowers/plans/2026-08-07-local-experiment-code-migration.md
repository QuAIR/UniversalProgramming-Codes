# Local Experiment Code Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Recover all locally backed-up experiment code and retained server artifacts, organize them into a reproducible public repository, verify them, and push the result to `QuAIR/UniversalProgramming-Codes`.

**Architecture:** Supported reusable routines live under `src/`, actual quair06 run definitions live under `experiments/`, retained numerical artifacts live under `results/`, and superseded or defective implementations live under `legacy/`. A machine-readable summary and a human-readable experiment manifest connect every reported value to its code and artifact. A standard-library Python verifier enforces layout, metadata, and sensitive-path rules without requiring MATLAB.

**Tech Stack:** MATLAB R2016b or newer, CVX 2.2, QETLAB 0.9, SDPT3 or MOSEK, optional YALMIP, Python 3 standard library, Git, PowerShell, and POSIX shell launch scripts for quair06.

## Global Constraints

- Recover source material from commit `4512790` in `D:/Program/6914205b76265c3b7d14df8b`.
- Do not access or mutate quair06 during this local-only migration.
- Preserve the exact qubit sample count `s = 500`; never reduce it in a published runner.
- Treat the `m=0,1` model as a lower-bound relaxation, not an exact reduction.
- Place the known defective general-d baseline and failed runs under `legacy/`.
- Preserve final `.mat` artifacts containing `p1`, `p2`, coefficient vectors, and qubit block data.
- Remove personal home paths, IP addresses, credentials, and license output from published text files.
- Do not add a license unless the repository owner selects one.
- Use ASCII for all newly written source and documentation.
- Push directly to the existing `main` branch after all checks pass.

---

### Task 1: Add Repository Verification and the Destination Skeleton

**Files:**
- Create: `tools/verify_repository.py`
- Create: `tests/python/test_verify_repository.py`
- Create: `.gitignore`

**Interfaces:**
- Consumes: the approved repository design.
- Produces: `verify_repository.validate_repository(root: pathlib.Path) -> list[str]`, where an empty list means the repository passes static validation.

- [ ] **Step 1: Write the failing standard-library verifier test**

```python
from pathlib import Path
import tempfile
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from verify_repository import validate_repository


class RepositoryVerifierTest(unittest.TestCase):
    def make_fixture(self, root):
        required = [
            "src/matlab/common/build_walled_brauer.m",
            "src/matlab/kcopy_d2/gamma_k_d2_exact.m",
            "experiments/quair06/kcopy_d2/run_exact_k14.m",
            "experiments/quair06/kcopy_d2/run_exact_k56.m",
            "docs/experiment-manifest.md",
            "legacy/README.md",
        ]
        for relative in required:
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("fixture\n", encoding="utf-8")
        artifact = root / "results/certified/example.mat"
        artifact.parent.mkdir(parents=True, exist_ok=True)
        artifact.write_bytes(b"MAT")
        (root / "results/summary.csv").write_text(
            "d,k,gamma,status,method,solver,sample_count,certificate,artifact\n"
            "2,1,5.5,validated,exact,sdpt3,500,baseline,results/certified/example.mat\n",
            encoding="utf-8",
        )
        for name in ("run_exact_k14.m", "run_exact_k56.m"):
            (root / "experiments/quair06/kcopy_d2" / name).write_text(
                "opts.s = 500;\n", encoding="utf-8"
            )

    def test_valid_fixture_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_fixture(root)
            self.assertEqual(validate_repository(root), [])

    def test_sensitive_path_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_fixture(root)
            (root / "README.md").write_text(
                "/home/" + "example/matlab_codes/cvx\n", encoding="utf-8"
            )
            self.assertTrue(validate_repository(root))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the test and verify the empty repository fails**

Run: `python -m unittest discover -s tests/python -v`

Expected: failure with `ModuleNotFoundError: No module named 'verify_repository'`.

- [ ] **Step 3: Implement the verifier**

`tools/verify_repository.py` must:

```python
TEXT_SUFFIXES = {".csv", ".log", ".m", ".md", ".py", ".sh", ".tex", ".txt", ".tsv"}
REQUIRED_SUMMARY_COLUMNS = [
    "d", "k", "gamma", "status", "method", "solver",
    "sample_count", "certificate", "artifact",
]
VALID_STATUSES = {"validated", "diagnostic", "legacy", "incomplete"}
```

The validator walks tracked-style text files while excluding `.git/`, rejects generic personal MATLAB home paths matching `/home/<user>/matlab_codes`, private IPv4 addresses, SSH private-key markers, CVX license URLs, and emitted `Username:` fields, validates the summary columns and statuses, checks that every nonempty `artifact` path exists, verifies that exact qubit runners contain `opts.s = 500`, and rejects any exact runner that calls `gamma_k_d2(...,'linear',...)`.

- [ ] **Step 4: Add repository ignore rules**

`.gitignore` must ignore MATLAB autosaves, crash dumps, generated partial results, PID files, temporary logs, Python caches, and local path configuration while allowing curated files below `results/`:

```gitignore
*.asv
matlab_crash_dump.*
__pycache__/
*.py[cod]
*.pid
*.nohup
*_partial.mat
*_partial.csv
local_config.m
.migration-staging/
```

- [ ] **Step 5: Commit the verification contract**

Run:

```powershell
git add .gitignore tools/verify_repository.py tests/python/test_verify_repository.py
git commit -m "Add repository verification contract"
```

### Task 2: Recover Shared Source and the Supported Qubit Solver

**Files:**
- Create: `src/matlab/common/build_walled_brauer.m`
- Create: `src/matlab/common/decompose_brauer_algebra.m`
- Create: `src/matlab/common/decompose_sector.m`
- Create: `src/matlab/common/random_SU.m`
- Create: `src/matlab/kcopy_d2/gamma_k_d2_exact.m`
- Create: `src/matlab/up_config.m`
- Create: `src/matlab/up_setup.m`
- Create: `src/python/irrep_dimensions.py`
- Create: `src/python/sk_invariance_reduction.py`
- Test: `tests/python/test_repository.py`

**Interfaces:**
- Consumes: historical files from `4512790:research_code/core/` and `4512790:research_code/kcopy_d2/gamma_k_d2_exact.m`.
- Produces: `[cost, info] = gamma_k_d2_exact(k, opts)`, `cfg = up_config(overrides)`, and `up_setup(cfg, requireYalmip)`.

- [ ] **Step 1: Extract the historical tree to an isolated staging directory**

Run with explicit paths:

```powershell
$sourceRepo = 'D:\Program\6914205b76265c3b7d14df8b'
$stageRoot = Join-Path $env:TEMP 'universal-programming-4512790'
New-Item -ItemType Directory -Force -Path $stageRoot | Out-Null
git -C $sourceRepo archive --format=tar --output="$stageRoot\research_code.tar" 4512790 research_code
tar -xf "$stageRoot\research_code.tar" -C $stageRoot
```

Expected: `$stageRoot/research_code` contains the full pre-removal source and result tree.

- [ ] **Step 2: Copy the reusable files to their destination paths**

Copy the four MATLAB helpers, two Python utilities, and corrected qubit solver listed in the Files section. Do not copy `core/gamma_k.m` into `src/`; it has a documented permutation defect and belongs in Task 5.

- [ ] **Step 3: Add portable configuration**

`up_config(overrides)` resolves the repository root from its own location and reads these optional environment variables:

```text
UP_CVX_ROOT
UP_QETLAB_ROOT
UP_YALMIP_ROOT
UP_MATLAB_BIN
UP_SDP_SOLVER
UP_RESULTS_ROOT
```

Defaults are an empty external dependency path, `matlab`, `sdpt3`, and `<repo>/results/generated`. Explicit fields in `overrides` take precedence over environment variables.

`up_setup(cfg, requireYalmip)` adds `src/matlab/common` and `src/matlab/kcopy_d2`, adds configured third-party roots, runs `cvx_setup` only when CVX is not already available, and raises identifiers `up_setup:missingCVX`, `up_setup:missingQETLAB`, or `up_setup:missingYALMIP` for missing required dependencies.

- [ ] **Step 4: Repair the solver's relocated helper path**

In `gamma_k_d2_exact.m`, change the default helper path from the obsolete sibling `../code` to `../common`. Preserve:

```matlab
defaults.s = 500;
defaults.certFresh = 50;
defaults.solver = 'sdpt3';
```

- [ ] **Step 5: Run source-level checks**

Run:

```powershell
python src/python/irrep_dimensions.py 2 2
python -m py_compile src/python/irrep_dimensions.py src/python/sk_invariance_reduction.py
python -m unittest discover -s tests/python -v
```

Expected: Python utilities compile and the isolated verifier tests pass.

- [ ] **Step 6: Commit supported source**

```powershell
git add src tests/python/test_repository.py
git commit -m "Restore portable SDP source"
```

### Task 3: Restore Exact Qubit Tests and quair06 Batch Definitions

**Files:**
- Create: `experiments/quair06/config/README.md`
- Create: `experiments/quair06/kcopy_d2/run_exact_k14.m`
- Create: `experiments/quair06/kcopy_d2/run_exact_k56.m`
- Create: `experiments/quair06/kcopy_d2/run_exact_k14.sh`
- Create: `experiments/quair06/kcopy_d2/run_exact_k56.sh`
- Create: `experiments/quair06/kcopy_d2/launch_exact_k14.sh`
- Create: `experiments/quair06/kcopy_d2/launch_exact_k56.sh`
- Create: `experiments/quair06/kcopy_d2/README.md`
- Create: `tests/matlab/test_exact_api.m`
- Create: `tests/matlab/test_exact_saved_blocks.m`
- Create: `tests/matlab/test_paths.m`
- Create: `tests/matlab/smoke_k1.m`

**Interfaces:**
- Consumes: `up_config`, `up_setup`, and `gamma_k_d2_exact` from Task 2.
- Produces: resumable batches for `k=1,...,4` and `k=5,6`, each saving one result per completed `k` plus a CSV summary.

- [ ] **Step 1: Port the MATLAB tests before the runners**

Recover the two historical exact tests and the `smoke_k1.m` baseline. Replace personal paths with:

```matlab
repoRoot = fileparts(fileparts(fileparts(mfilename('fullpath'))));
addpath(fullfile(repoRoot, 'src', 'matlab'));
cfg = up_config();
up_setup(cfg, false);
```

`test_paths.m` asserts that `build_walled_brauer`, `decompose_sector`, and `gamma_k_d2_exact` resolve inside the current repository.

- [ ] **Step 2: Port the exact batch scripts**

Recover the historical `run_quair06_exact_k14.m` and `run_quair06_exact_k56.m`, rename them as listed, and initialize paths through `up_config` and `up_setup`. Both runners set:

```matlab
opts.s = 500;
opts.saveResult = true;
opts.solver = cfg.solver;
```

The `k=1,...,4` runner checks `abs(cost - 5.5) < 1e-5` at `k=1`. Both runners save partial summary data after every completed value and keep all block-level fields written by `gamma_k_d2_exact`.

- [ ] **Step 3: Port the shell wrappers**

Each wrapper resolves the repository root relative to the script, obtains the MATLAB binary from `${UP_MATLAB_BIN:-matlab}`, creates `${UP_RESULTS_ROOT:-<repo>/results/generated}`, runs MATLAB with `-batch`, and propagates its exit status. Launch scripts use `nohup`, write PID and log files below the generated output directory, and never contain a hostname or user path.

- [ ] **Step 4: Verify exact-runner isolation**

Run:

```powershell
Select-String -Path experiments\quair06\kcopy_d2\* -Pattern "linear|/home/|private-address"
python tools/verify_repository.py
```

Expected: no exact runner invokes the linear model; any occurrence of `linear` is explanatory prose only; the verifier reports only not-yet-restored manifest/results failures.

- [ ] **Step 5: Run MATLAB checks when available**

Run `Get-Command matlab -ErrorAction SilentlyContinue`. If MATLAB is installed, execute:

```powershell
matlab -batch "run('tests/matlab/test_paths.m')"
```

Run the CVX-dependent `test_exact_api.m` only when configured CVX and QETLAB are available locally. Record unavailable proprietary dependencies rather than lowering solver precision or sample count.

- [ ] **Step 6: Commit exact qubit experiments**

```powershell
git add experiments/quair06/config experiments/quair06/kcopy_d2 tests/matlab
git commit -m "Restore exact qubit experiment batches"
```

### Task 4: Restore General-Dimension Server Experiment Code

**Files:**
- Create: `experiments/quair06/general_d/README.md`
- Create: `experiments/quair06/general_d/cert_d2_k3.m`
- Create: `experiments/quair06/general_d/cert_d2_k4.m`
- Create: `experiments/quair06/general_d/cert_d4_k2.m`
- Create: `experiments/quair06/general_d/cert_d5_k2.m`
- Create: `experiments/quair06/general_d/gamma_struct3.m`
- Create: `experiments/quair06/general_d/gamma_y3.m`
- Create: `experiments/quair06/general_d/validate_fastP.m`
- Create: `experiments/quair06/general_d/diagnostics/fit_analytic.py`
- Create: `experiments/quair06/general_d/diagnostics/gamma_struct.m`
- Create: `experiments/quair06/general_d/diagnostics/gamma_struct2.m`
- Create: `experiments/quair06/general_d/diagnostics/gamma_y.m`
- Create: `experiments/quair06/general_d/diagnostics/probe_d4k4.m`

**Interfaces:**
- Consumes: the exact historical server scripts in `4512790:research_code/results/`.
- Produces: portable snapshots of every locally backed-up general-d server experiment, separated into validated and diagnostic groups.

- [ ] **Step 1: Copy every MATLAB and Python experiment script**

Use the mapping in the Files section. Preserve numerical parameters and solver settings. Do not rewrite mathematical assembly code during this migration.

- [ ] **Step 2: Replace external absolute paths with configuration calls**

At each script entry point, resolve the repository root, add `src/matlab`, obtain `cfg = up_config()`, and call `up_setup(cfg, false)` or `up_setup(cfg, true)` for YALMIP scripts. Preserve `mosek` where the historical run used MOSEK; report its requirement in the README.

- [ ] **Step 3: Document support status**

The README identifies `gamma_struct3.m`, `gamma_y3.m`, the four `cert_*.m` files, and `validate_fastP.m` as retained validated-run snapshots. It identifies the `diagnostics/` files as intermediate formulations or probes and lists their corresponding result names.

- [ ] **Step 4: Scan for personal paths and syntax damage**

Run:

```powershell
python tools/verify_repository.py
Get-ChildItem -Recurse -File experiments\quair06\general_d | Select-String -Pattern "/home/|private-address|research-user"
```

Expected: no matches for personal paths; verifier failures are limited to later documentation and result tasks.

- [ ] **Step 5: Commit general-d experiments**

```powershell
git add experiments/quair06/general_d
git commit -m "Restore general-d server experiments"
```

### Task 5: Preserve Superseded, Defective, and Failed Code

**Files:**
- Create: `legacy/README.md`
- Create: `legacy/general-d-baseline/gamma_k.m`
- Create: `legacy/general-d-baseline/README.md`
- Create: `legacy/general-d-baseline/decompose_brauer_algebra.m`
- Create: `legacy/general-d-baseline/generators/gen.sh`
- Create: `legacy/general-d-baseline/generators/genfast.sh`
- Create: `legacy/general-d-baseline/generators/genbrute.sh`
- Create: `legacy/qubit-reduced-prototype/gamma_k_d2.m`
- Create: `legacy/qubit-reduced-prototype/run_kcopy_d2.m`
- Create: `legacy/qubit-reduced-prototype/run_quair06_k14.m`
- Create: `legacy/qubit-reduced-prototype/run_quair06_k14.sh`
- Create: `legacy/qubit-reduced-prototype/launch_quair06_k14.sh`
- Create: `legacy/qubit-reduced-prototype/README.md`
- Create: `legacy/linear-relaxation/run_quair06_linear_k14.m`
- Create: `legacy/linear-relaxation/run_quair06_linear_k14.sh`
- Create: `legacy/linear-relaxation/launch_quair06_linear_k14.sh`
- Create: `legacy/linear-relaxation/README.md`
- Create: `legacy/failed-runs/fixed_protocol_cost_check.m`
- Create: `legacy/failed-runs/README.md`

**Interfaces:**
- Consumes: superseded historical source plus the recoverable server-only fixed-protocol script from the local execution record.
- Produces: a complete but non-primary provenance archive with explicit warnings.

- [ ] **Step 1: Copy historical legacy files without silently correcting their mathematics**

Keep the original algorithmic bodies. Replace only sensitive absolute paths in executable wrappers. Put the obsolete algebra decomposition copy beside the defective baseline because the historical generator pipeline depended on that version.

- [ ] **Step 2: Recover the fixed-protocol diagnostic**

Create `fixed_protocol_cost_check.m` from the recorded server script. Make CVX setup use `up_config` and `up_setup`. Retain the loop through `k=3`; document the observed results:

```text
k=1: 5.500000001339, Solved
k=2: 3.666666669558, Solved
k=3: MATLAB terminated during the attempted run
```

- [ ] **Step 3: Write explicit status warnings**

The legacy READMEs state:

- `gamma_k.m` has the documented `PermuteSystems` convention defect for `k>=3` and is not a supported entry point;
- `gamma_k_d2.m` contains a full raw-row mode and an `m=0,1` mode, but only the latter is the linear relaxation;
- the linear relaxation can be below the exact optimum and must not be cited as `gamma_k`;
- failed and under-sampled runs are retained only for provenance.

- [ ] **Step 4: Verify primary code does not depend on legacy code**

Run:

```powershell
Get-ChildItem -Recurse -File src,experiments | Select-String -Pattern "legacy/|legacy\\|gamma_k_d2\(.*linear"
python tools/verify_repository.py
```

Expected: no primary source imports a legacy path or invokes the linear solver.

- [ ] **Step 5: Commit the provenance archive**

```powershell
git add legacy
git commit -m "Archive superseded experiment implementations"
```

### Task 6: Restore Results, Mathematical Notes, and Figure Reproduction

**Files:**
- Create: `results/README.md`
- Create: `results/summary.csv`
- Create: `results/certified/general_d/*.mat`
- Create: `results/certified/strict_submult_C_sparse.tsv`
- Create: `results/certified/README.md`
- Create: `results/certified/kcopy_d2/exact_d2_k1.mat`
- Create: `results/certified/kcopy_d2/exact_d2_k2.mat`
- Create: `results/certified/kcopy_d2/exact_d2_k3.mat`
- Create: `results/certified/kcopy_d2/exact_d2_k4.mat`
- Create: `results/diagnostic/*.mat`
- Create: `results/diagnostic/sk_invariance_output.txt`
- Create: `results/logs/*.log`
- Create: `docs/mathematical-reduction/kcopy_d2_reduction.tex`
- Create: `docs/mathematical-reduction/MATH_REFERENCE.md`
- Create: `docs/provenance/quair06-rerun-plan.md`
- Create: `docs/provenance/RESULTS_d3.md`
- Create: `docs/provenance/server-status-2026-06-13.md`
- Create: `figures/fig3_kcopy_decay_data.csv`
- Create: `figures/make_fig3_kcopy_decay.py`

**Interfaces:**
- Consumes: result artifacts, selected logs, mathematical sources, and figure files from `4512790:research_code/`.
- Produces: a complete local evidence package for all retained code and the manuscript's numerical table.

- [ ] **Step 1: Copy final and diagnostic binary artifacts**

Copy all historical `.mat` files and the sparse strict-submultiplicativity certificate. Classify these as final validated artifacts:

```text
cert_d2_k3.mat
cert_d2_k4.mat
cert_d4_k2.mat
cert_d5_k2.mat
struct2_d2_k5.mat
struct2_d3_k3.mat
struct3_d4_k3.mat
y3_d4_k4.mat
y3_d5_k3.mat
exact_d2_k1.mat
exact_d2_k2.mat
exact_d2_k3.mat
exact_d2_k4.mat
```

Place all other retained `.mat` files under `results/diagnostic/` without renaming their internal variables.

- [ ] **Step 2: Build the canonical numerical summary**

Create `results/summary.csv` with the exact header from Task 1 and rows for the validated values:

```text
d=2: k=1 5.500000; k=2 2.713330; k=3 1.888291; k=4 1.529423; k=5 1.350907
d=3: k=1 15.222222; k=2 7.456450; k=3 4.882170; k=4 3.619643
d=4: k=1 29.125000; k=2 14.366215; k=3 9.453850; k=4 7.003853
d=5: k=1 47.080000; k=2 23.324402; k=3 15.410364
```

Use status `validated` except `d=3,k=4`, whose status is `diagnostic` because it rests on two-engine agreement rather than a full certificate. Point each row to an existing artifact; where the historical backup contains no separate `.mat` for `k=1`, point to the formula description in `results/README.md` only by leaving `artifact` empty.

- [ ] **Step 3: Sanitize and classify logs**

Copy only logs needed to support retained results or explain failed runs. Replace personal home paths with `<HOME>`, private addresses with `<QUAIR06>`, remove CVX license URLs and usernames, and retain solver status, objective, timings, and residual lines. Move failed or under-sampled logs below `legacy/failed-runs/logs/`.

- [ ] **Step 4: Restore mathematical and figure sources**

Copy the corrected reduction TeX, mathematical reference, figure CSV, and figure Python script. Update only repository-relative paths. Do not commit `kcopy_d2_upload.tgz` or the generated reduction PDF because both are reproducible duplicates.

- [ ] **Step 5: Verify binary variables when MATLAB or SciPy is available**

First load the bundled workspace dependencies. If SciPy is available, inspect all non-v7.3 `.mat` files and confirm final artifact keys. For v7.3 files, use `h5py` when available. Otherwise use MATLAB `whos('-file', path)` if MATLAB is installed. The four exact qubit files must expose the saved objective and block data described by the solver version that produced them; record any older schema accurately in `results/README.md` rather than fabricating missing fields.

- [ ] **Step 6: Commit evidence and reproduction material**

```powershell
git add results docs/mathematical-reduction docs/provenance figures legacy/failed-runs/logs
git commit -m "Restore experiment results and derivation sources"
```

### Task 7: Write the Public Documentation and Experiment Manifest

**Files:**
- Modify: `README.md`
- Create: `docs/experiment-manifest.md`
- Create: `experiments/quair06/README.md`
- Create: `tests/python/test_repository.py`
- Modify: component READMEs from Tasks 3-6

**Interfaces:**
- Consumes: all code and artifacts restored in prior tasks.
- Produces: a reader-facing map from scientific claim to command, source, result, and status.

- [ ] **Step 1: Write the root README**

The README contains:

- project scope and the definition of the retained programming-cost computation;
- a status warning distinguishing exact, diagnostic, legacy, and incomplete material;
- repository layout;
- MATLAB/CVX/QETLAB/YALMIP requirements;
- environment-variable configuration;
- the exact qubit quick start;
- quair06 batch commands;
- test and verification commands;
- the canonical numerical table linked to `results/summary.csv`;
- a statement that no live quair06 reconciliation was performed in this local-only phase.

- [ ] **Step 2: Write one manifest entry per experiment family**

Each `docs/experiment-manifest.md` entry includes:

```text
Identifier
Status: validated | diagnostic | legacy | incomplete
Dimensions and copy counts
Entry script
Dependencies and solver
Sample count
Output artifacts
Certificate or residual checks
Historical source: commit 4512790 path or recovered execution record
Known limitations
```

Cover exact qubit `k=1,...,4`, incomplete local record for exact `k=5,6`, the linear relaxation, general-d structured CVX runs, YALMIP runs, certificates, brute/under-sampled diagnostics, and the fixed-protocol cost check.

- [ ] **Step 3: Add local and server run instructions**

`experiments/quair06/README.md` documents the environment variables and shows:

```bash
export UP_CVX_ROOT=/path/to/cvx
export UP_QETLAB_ROOT=/path/to/QETLAB-0.9
export UP_RESULTS_ROOT=/path/to/output
./experiments/quair06/kcopy_d2/launch_exact_k14.sh
```

The path values are illustrative examples in documentation only and are not committed configuration.

- [ ] **Step 4: Add the complete-repository integration test**

```python
from pathlib import Path
import csv
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from verify_repository import validate_repository


class RepositoryIntegrationTest(unittest.TestCase):
    def test_required_entry_points_exist(self):
        for relative in (
            "src/matlab/common/build_walled_brauer.m",
            "src/matlab/kcopy_d2/gamma_k_d2_exact.m",
            "experiments/quair06/kcopy_d2/run_exact_k14.m",
            "experiments/quair06/kcopy_d2/run_exact_k56.m",
            "results/summary.csv",
            "docs/experiment-manifest.md",
            "legacy/README.md",
        ):
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_summary_schema(self):
        with (ROOT / "results/summary.csv").open(newline="", encoding="utf-8") as handle:
            self.assertEqual(
                csv.DictReader(handle).fieldnames,
                ["d", "k", "gamma", "status", "method", "solver", "sample_count", "certificate", "artifact"],
            )

    def test_static_verifier(self):
        self.assertEqual(validate_repository(ROOT), [])
```

- [ ] **Step 5: Run link, metadata, and sensitive-data verification**

Run:

```powershell
python tools/verify_repository.py
python -m unittest discover -s tests/python -v
git grep -n -I -E "(/home/[A-Za-z0-9_.-]+/matlab_codes|BEGIN OPENSSH PRIVATE KEY|cvx/academic\?)"
```

Expected: verifier and unit tests pass; sensitive grep has no matches.

- [ ] **Step 6: Commit public documentation**

```powershell
git add README.md docs/experiment-manifest.md experiments/quair06/README.md experiments/quair06/*/README.md results/README.md legacy/*/README.md tests/python/test_repository.py
git commit -m "Document experiment reproducibility and provenance"
```

### Task 8: Final Validation and GitHub Synchronization

**Files:**
- Modify only files required to fix validation findings.
- Verify: entire repository.

**Interfaces:**
- Consumes: the complete local migration.
- Produces: a verified `main` branch pushed to `origin/main`.

- [ ] **Step 1: Compare the recovered code inventory with the destination**

List every `.m`, `.py`, and `.sh` file under the historical `research_code` tree and account for it in `src/`, `experiments/`, or `legacy/`. Confirm the server-only fixed-protocol check is also present. Record the mapping in the final report.

- [ ] **Step 2: Run all available tests**

```powershell
python -m unittest discover -s tests/python -v
python tools/verify_repository.py
python -m py_compile src/python/irrep_dimensions.py src/python/sk_invariance_reduction.py figures/make_fig3_kcopy_decay.py experiments/quair06/general_d/diagnostics/fit_analytic.py
git diff --check origin/main...HEAD
git status --short --branch
```

If MATLAB is installed, additionally run `tests/matlab/test_paths.m`; run CVX tests only when local CVX and QETLAB are configured.

- [ ] **Step 3: Review repository size and tracked binary set**

Use `git ls-files` and file sizes to confirm there are no upload tarballs, generated PDFs, caches, partial outputs, crash dumps, or unexpectedly large files. Confirm every tracked `.mat` file is described in `results/README.md` or the experiment manifest.

- [ ] **Step 4: Inspect the complete diff and recent commits**

```powershell
git diff --stat origin/main...HEAD
git log --oneline --decorate origin/main..HEAD
```

Expected: only the approved repository migration and its design/plan commits are ahead of `origin/main`.

- [ ] **Step 5: Push the verified branch**

```powershell
git push origin main
```

Expected: `origin/main` advances to the final local commit.

- [ ] **Step 6: Report deferred remote reconciliation**

State that quair06 was intentionally not accessed in this phase. The later remote pass must checksum `~/projects/kcopy_d2`, recover any newer `k=5,6` files, update the manifest and results, rerun verification, and push a separate commit.
