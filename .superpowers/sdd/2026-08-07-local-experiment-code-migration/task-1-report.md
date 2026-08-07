# Task 1 Report: Repository Verification and Destination Skeleton

## What You Implemented

- Added `tools/verify_repository.py` with `validate_repository(root: Path) -> list[str]`.
- The verifier checks required repository entry points, tracked-style text content outside `.git/`, sensitive paths and credentials, the results-summary schema and artifact references, and exact-runner safeguards.
- Added the required standard-library tests and repository ignore rules.

## Exact Tests and Results

| Command | Result |
| --- | --- |
| `python -m unittest discover -s tests/python -p test_verify_repository.py -v` | Passed: 2 tests. |
| `python -m unittest discover -s tests/python -v` | Passed: 2 tests. |
| `python -m py_compile tools/verify_repository.py` | Passed. |
| `git diff --check` | Passed with no whitespace errors. |

The command-line verifier was also run against the current repository. It correctly failed because later-task source, experiments, manifest, legacy, and result files have not yet been restored.

## TDD Evidence

### RED

After adding only `tests/python/test_verify_repository.py`, `python -m unittest discover -s tests/python -v` failed with the expected `ModuleNotFoundError: No module named 'verify_repository'`.

### GREEN

After adding the verifier and ignore rules, the focused and full Python test commands both passed all 2 tests. An initial GREEN attempt exposed an invalid regular-expression escape during import; the pattern literals were corrected and the same tests then passed.

## Files Changed

- `.gitignore`
- `tools/verify_repository.py`
- `tests/python/test_verify_repository.py`

## Self-Review Findings

- The implementation uses only Python standard-library modules.
- The required constants, summary columns, valid statuses, ignore entries, artifact checks, and exact-runner checks match the task brief.
- The committed diff passed Git whitespace validation.

## Concerns

- The repository-wide verifier is not expected to pass until later migration tasks create the required source, runner, documentation, legacy, and results files.
- Existing migration-planning documents under `.superpowers/` and `docs/superpowers/` contain literal examples of prohibited markers, so the current root-level CLI invocation also reports those files. This task does not alter those unrelated planning documents.

## Commit

- `1074f00 Add repository verification contract`

## Fix Round 1

### Changes

- Checked every literal `opts.s` assignment in exact runners and reject values below 500, including later overrides.
- Broadened publication checks to real POSIX and Windows personal home paths, valid IPv4 addresses, and generic PEM private-key markers. Angle-bracket home-directory placeholders remain allowed.
- Excluded the git-ignored root `.superpowers/` workspace from text publication scanning while continuing to scan tracked-style repository files.
- Replaced the flat linear-call regular expression with balanced-parenthesis parsing, so nested and multiline `gamma_k_d2(..., 'linear', ...)` calls are rejected.
- Added a legacy documentation rule: when a legacy linear mode, linear relaxation, or `m = 0,1` reference exists, the documentation must include lower-bound and not-equivalent wording.

### Covering Tests

- `tests/python/test_verify_repository.py`
  - invalid summary columns, invalid summary status, and missing artifacts
  - later sample-count override and nested-expression linear calls
  - personal-home paths, IP addresses, generic private-key markers, `.superpowers/` exclusion, and angle-bracket home-path placeholders
  - legacy linear-relaxation labeling

### Exact Commands and Outputs

```text
python -m unittest discover -s tests/python -p test_verify_repository.py -v
Ran 10 tests in 0.217s
OK

python -m unittest discover -s tests/python -v
Ran 10 tests in 0.224s
OK

python -m py_compile tools/verify_repository.py tests/python/test_verify_repository.py
No output; exit 0

git diff --check
No whitespace errors; exit 0
```

### Repository Verifier Check

```text
python tools/verify_repository.py
Repository verification failed only for the seven destination files not yet created by later migration tasks:
src/matlab/common/build_walled_brauer.m
src/matlab/kcopy_d2/gamma_k_d2_exact.m
experiments/quair06/kcopy_d2/run_exact_k14.m
experiments/quair06/kcopy_d2/run_exact_k56.m
docs/experiment-manifest.md
legacy/README.md
results/summary.csv
```

The scan no longer reports prohibited literals from `.superpowers/` or the verifier's own regression fixtures.

## Fix Round 2

### Changes

- Narrowed the ignored scratch workspace from all of `.superpowers/` to only `.superpowers/sdd/`; other `.superpowers` subtrees are scanned as tracked-style text.
- Restored the exact-runner sample contract: at least one literal `opts.s = 500;` assignment is required, and any literal assignment below 500 is rejected, including a later override.

### Covering Tests

- `test_superpowers_sdd_is_excluded_and_placeholder_home_path_is_allowed`
- `test_superpowers_policy_file_is_scanned`
- `test_sample_count_of_600_without_500_fails`
- `test_later_sample_count_override_fails`

### Exact Commands and Outputs

```text
python -m unittest discover -s tests/python -p test_verify_repository.py -v
Ran 12 tests in 0.298s
OK

python -m unittest discover -s tests/python -v
Ran 12 tests in 0.294s
OK

python -m py_compile tools/verify_repository.py tests/python/test_verify_repository.py
No output; exit 0

git diff --check
No output; exit 0
```
