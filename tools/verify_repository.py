"""Static checks for the public experiment-code repository."""

import csv
import hashlib
import json
from pathlib import Path
import re


TEXT_SUFFIXES = {
    ".csv", ".json", ".log", ".m", ".md", ".py", ".sh", ".tex", ".txt", ".tsv"
}
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
    "results/mat-artifacts.json",
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
CERT_FRESH_ASSIGNMENT = re.compile(
    r"(?im)^\s*opts\s*\.\s*certFresh\s*=\s*([0-9]+)\s*;"
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
        if relative.parts and relative.parts[0] == ".git":
            continue
        if relative.parts[:2] == (".superpowers", "sdd"):
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


def _validate_mat_manifest(root: Path, errors: list[str]) -> dict[str, dict]:
    manifest_path = root / "results/mat-artifacts.json"
    if not manifest_path.is_file():
        return {}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"results/mat-artifacts.json: cannot parse manifest: {exc}")
        return {}

    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list):
        errors.append("results/mat-artifacts.json: artifacts must be a list")
        return {}
    if manifest.get("artifact_count") != len(artifacts):
        errors.append("results/mat-artifacts.json: artifact_count mismatch")

    by_path = {}
    for entry in artifacts:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            errors.append("results/mat-artifacts.json: artifact entry lacks a path")
            continue
        relative = entry["path"]
        relative_path = Path(relative)
        if (
            "\\" in relative
            or relative_path.is_absolute()
            or ".." in relative_path.parts
            or relative_path.parts[:1] != ("results",)
            or relative_path.suffix.lower() != ".mat"
        ):
            errors.append(f"results/mat-artifacts.json: invalid artifact path {relative}")
            continue
        if relative in by_path:
            errors.append(f"results/mat-artifacts.json: duplicate artifact {relative}")
            continue
        by_path[relative] = entry
        path = root / relative
        if not path.is_file():
            errors.append(f"{relative}: artifact listed in manifest is missing")
            continue
        expected_digest = entry.get("current_sha256")
        actual_digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if expected_digest != actual_digest:
            errors.append(f"{relative}: SHA-256 does not match mat-artifacts.json")
        variables = entry.get("variables")
        if not isinstance(variables, list) or not variables:
            errors.append(f"{relative}: artifact manifest has no variables")
        if entry.get("classification") not in {"certified", "diagnostic"}:
            errors.append(f"{relative}: invalid artifact classification")

    actual_mats = {
        path.relative_to(root).as_posix()
        for path in (root / "results").rglob("*.mat")
        if path.is_file()
    }
    for relative in sorted(actual_mats - set(by_path)):
        errors.append(f"{relative}: MAT artifact is absent from mat-artifacts.json")
    for relative in sorted(set(by_path) - actual_mats):
        if (root / relative).is_file():
            errors.append(f"{relative}: manifest entry is not a results MAT artifact")
    return by_path


def _validate_summary(
    root: Path, errors: list[str], mat_artifacts: dict[str, dict]
) -> None:
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
            if not artifact.endswith(".mat"):
                continue
            entry = mat_artifacts.get(artifact)
            if entry is None:
                errors.append(
                    f"results/summary.csv:{line_number}: MAT artifact is absent "
                    "from mat-artifacts.json"
                )
                continue
            if status == "validated" and entry.get("classification") != "certified":
                errors.append(
                    f"results/summary.csv:{line_number}: validated row references "
                    "diagnostic MAT artifact"
                )
            evidence = entry.get("evidence", {})
            expected = {
                "d": row["d"],
                "k": row["k"],
                "cost": row["gamma"],
                "sample_count": row["sample_count"],
            }
            for field, text_value in expected.items():
                if field not in evidence:
                    errors.append(
                        f"results/summary.csv:{line_number}: MAT evidence lacks {field}"
                    )
                    continue
                try:
                    if field in {"d", "k", "sample_count"}:
                        matches = int(evidence[field]) == int(text_value)
                    else:
                        matches = abs(float(evidence[field]) - float(text_value)) <= 1e-5
                except (TypeError, ValueError):
                    matches = False
                if not matches:
                    errors.append(
                        f"results/summary.csv:{line_number}: MAT evidence {field} mismatch"
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
        if 500 not in sample_counts:
            errors.append(f"{relative}: missing opts.s = 500")
        if any(sample_count < 500 for sample_count in sample_counts):
            errors.append(f"{relative}: opts.s is below 500")
        cert_fresh_values = [
            int(value) for value in CERT_FRESH_ASSIGNMENT.findall(content)
        ]
        if 50 not in cert_fresh_values:
            errors.append(f"{relative}: missing opts.certFresh = 50")
        if any(cert_fresh < 50 for cert_fresh in cert_fresh_values):
            errors.append(f"{relative}: opts.certFresh is below 50")
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
    mat_artifacts = _validate_mat_manifest(root, errors)
    _validate_summary(root, errors, mat_artifacts)
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
