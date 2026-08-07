"""Static checks for the public experiment-code repository."""

import csv
from pathlib import Path
import re


TEXT_SUFFIXES = {".csv", ".log", ".m", ".md", ".py", ".sh", ".tex", ".txt", ".tsv"}
REQUIRED_SUMMARY_COLUMNS = [
    "d", "k", "gamma", "status", "method", "solver",
    "sample_count", "certificate", "artifact",
]
VALID_STATUSES = {"validated", "diagnostic", "legacy", "incomplete"}

REQUIRED_FILES = (
    "src/matlab/common/build_walled_brauer.m",
    "src/matlab/kcopy_d2/gamma_k_d2_exact.m",
    "experiments/quair06/kcopy_d2/run_exact_k14.m",
    "experiments/quair06/kcopy_d2/run_exact_k56.m",
    "docs/experiment-manifest.md",
    "legacy/README.md",
    "results/summary.csv",
)
EXACT_RUNNERS = (
    "experiments/quair06/kcopy_d2/run_exact_k14.m",
    "experiments/quair06/kcopy_d2/run_exact_k56.m",
)
PERSONAL_MATLAB_HOME = re.compile(r"/home/[^/\s]+/matlab_codes")
PRIVATE_ADDRESS = re.compile(r"(?<![0-9.])10\.4\.6\.[0-9]{1,3}(?![0-9.])")
CVX_LICENSE_URL = re.compile(
    r"https?://[^\s\"']*(?:cvxr\.com/cvx/academic|cvx[^\s\"']*license)",
    re.IGNORECASE,
)
USERNAME_FIELD = re.compile(r"(?m)^\s*Username:\s*")
LINEAR_EXACT_CALL = re.compile(r"gamma_k_d2\s*\([^)]*['\"]linear['\"]", re.IGNORECASE)
PRIVATE_KEY_MARKERS = tuple(
    "BEGIN " + key_type + " PRIVATE KEY"
    for key_type in ("OPENSSH", "RSA", "EC", "DSA")
)


def _text_files(root: Path):
    for path in root.rglob("*"):
        if ".git" in path.relative_to(root).parts:
            continue
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def _validate_sensitive_text(root: Path, errors: list[str]) -> None:
    checks = (
        (PERSONAL_MATLAB_HOME, "personal MATLAB home path"),
        (PRIVATE_ADDRESS, "private 10.4.6.* address"),
        (CVX_LICENSE_URL, "CVX license URL"),
        (USERNAME_FIELD, "Username field"),
    )
    for path in _text_files(root):
        content = path.read_text(encoding="utf-8", errors="replace")
        relative = path.relative_to(root)
        for pattern, description in checks:
            if pattern.search(content):
                errors.append(f"{relative}: contains {description}")
        if any(marker in content for marker in PRIVATE_KEY_MARKERS):
            errors.append(f"{relative}: contains SSH private-key marker")


def _validate_summary(root: Path, errors: list[str]) -> None:
    summary = root / "results/summary.csv"
    if not summary.is_file():
        return

    with summary.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != REQUIRED_SUMMARY_COLUMNS:
            errors.append("results/summary.csv: invalid summary columns")
            return
        for line_number, row in enumerate(reader, start=2):
            status = row["status"]
            if status not in VALID_STATUSES:
                errors.append(
                    f"results/summary.csv:{line_number}: invalid status {status!r}"
                )
            artifact = row["artifact"].strip()
            if artifact and not (root / artifact).is_file():
                errors.append(
                    f"results/summary.csv:{line_number}: missing artifact {artifact}"
                )


def _validate_exact_runners(root: Path, errors: list[str]) -> None:
    for relative in EXACT_RUNNERS:
        runner = root / relative
        if not runner.is_file():
            continue
        content = runner.read_text(encoding="utf-8", errors="replace")
        if "opts.s = 500" not in content:
            errors.append(f"{relative}: missing opts.s = 500")
        if LINEAR_EXACT_CALL.search(content):
            errors.append(f"{relative}: exact runner invokes gamma_k_d2 linear mode")


def validate_repository(root: Path) -> list[str]:
    """Return static validation failures for *root*, or an empty list."""
    errors = []
    for relative in REQUIRED_FILES:
        if not (root / relative).is_file():
            errors.append(f"missing required file: {relative}")
    _validate_sensitive_text(root, errors)
    _validate_summary(root, errors)
    _validate_exact_runners(root, errors)
    return errors


if __name__ == "__main__":
    repository_root = Path(__file__).resolve().parents[1]
    failures = validate_repository(repository_root)
    if failures:
        print("Repository verification failed:")
        for failure in failures:
            print(f"- {failure}")
        raise SystemExit(1)
    print("Repository verification passed.")
