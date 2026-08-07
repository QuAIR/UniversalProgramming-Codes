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
POSIX_PERSONAL_HOME = re.compile(
    r"(?<![\w/])/(?:home|Users)/[A-Za-z0-9][A-Za-z0-9._-]*(?=/|$)"
)
WINDOWS_PERSONAL_HOME = re.compile(
    r"(?<![\w\\])[A-Za-z]:\\Users\\[A-Za-z0-9][A-Za-z0-9._-]*(?=\\|$)",
    re.IGNORECASE,
)
IP_ADDRESS = re.compile(
    r"(?<![0-9.])(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])"
    r"(?:\.(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])){3}(?![0-9.])"
)
CVX_LICENSE_URL = re.compile(
    r"https?://[^\s\"']*(?:cvxr\.com/cvx/academic|cvx[^\s\"']*license)",
    re.IGNORECASE,
)
USERNAME_FIELD = re.compile(r"(?m)^\s*Username:\s*")
SAMPLE_COUNT_ASSIGNMENT = re.compile(
    r"(?im)^\s*opts\s*\.\s*s\s*=\s*([0-9]+)\s*;"
)
LINEAR_ARGUMENT = re.compile(r"['\"]linear['\"]", re.IGNORECASE)
LINEAR_RELAXATION_REFERENCE = re.compile(
    r"\blinear[- ](?:mode|relaxation)\b|\bm\s*=\s*0\s*,\s*1\b",
    re.IGNORECASE,
)
PRIVATE_KEY_MARKER = re.compile(
    r"-----BEGIN (?:[A-Z0-9]+ )?PRIVATE KEY-----"
)
LOWER_BOUND_WORDING = re.compile(r"\blower[- ]bound\b", re.IGNORECASE)
NOT_EQUIVALENT_WORDING = re.compile(r"\bnot[- ]equivalent\b", re.IGNORECASE)


def _text_files(root: Path):
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if relative.parts and relative.parts[0] in {".git", ".superpowers"}:
            continue
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def _validate_sensitive_text(root: Path, errors: list[str]) -> None:
    checks = (
        (POSIX_PERSONAL_HOME, "personal home path"),
        (WINDOWS_PERSONAL_HOME, "personal home path"),
        (IP_ADDRESS, "IP address"),
        (CVX_LICENSE_URL, "CVX license URL"),
        (USERNAME_FIELD, "Username field"),
    )
    for path in _text_files(root):
        content = path.read_text(encoding="utf-8", errors="replace")
        relative = path.relative_to(root)
        for pattern, description in checks:
            if pattern.search(content):
                errors.append(f"{relative}: contains {description}")
        if PRIVATE_KEY_MARKER.search(content):
            errors.append(f"{relative}: contains private-key marker")


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
        sample_counts = [
            int(value) for value in SAMPLE_COUNT_ASSIGNMENT.findall(content)
        ]
        if not sample_counts:
            errors.append(f"{relative}: missing opts.s = 500")
        elif any(sample_count < 500 for sample_count in sample_counts):
            errors.append(f"{relative}: opts.s is below 500")
        if any(
            LINEAR_ARGUMENT.search(args)
            for args in _function_calls(content, "gamma_k_d2")
        ):
            errors.append(f"{relative}: exact runner invokes gamma_k_d2 linear mode")


def _function_calls(content: str, name: str):
    call_start = re.compile(rf"\b{re.escape(name)}\s*\(")
    for match in call_start.finditer(content):
        depth = 1
        quote = None
        index = match.end()
        arguments_start = index
        while index < len(content) and depth:
            character = content[index]
            if quote:
                if character == quote:
                    if (
                        quote == "'"
                        and index + 1 < len(content)
                        and content[index + 1] == quote
                    ):
                        index += 2
                        continue
                    quote = None
            elif character in "'\"":
                quote = character
            elif character == "(":
                depth += 1
            elif character == ")":
                depth -= 1
            index += 1
        if depth == 0:
            yield content[arguments_start:index - 1]


def _validate_linear_relaxation_documentation(root: Path, errors: list[str]) -> None:
    legacy = root / "legacy"
    if not legacy.is_dir():
        return

    documentation = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in _text_files(legacy)
    )
    if LINEAR_RELAXATION_REFERENCE.search(documentation) and (
        not LOWER_BOUND_WORDING.search(documentation)
        or not NOT_EQUIVALENT_WORDING.search(documentation)
    ):
        errors.append(
            "legacy: linear-relaxation documentation must state lower-bound "
            "and not-equivalent wording"
        )


def validate_repository(root: Path) -> list[str]:
    """Return static validation failures for *root*, or an empty list."""
    errors = []
    for relative in REQUIRED_FILES:
        if not (root / relative).is_file():
            errors.append(f"missing required file: {relative}")
    _validate_sensitive_text(root, errors)
    _validate_summary(root, errors)
    _validate_exact_runners(root, errors)
    _validate_linear_relaxation_documentation(root, errors)
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
