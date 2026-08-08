import hashlib
import json
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
            "experiments/server/kcopy_d2/run_exact_k14.m",
            "experiments/server/kcopy_d2/run_exact_k56.m",
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
        (root / "results/mat-artifacts.json").write_text(
            json.dumps(
                {
                    "schema_version": 2,
                    "artifact_count": 1,
                    "artifacts": [
                        {
                            "path": "results/certified/example.mat",
                            "classification": "certified",
                            "current_sha256": hashlib.sha256(b"MAT").hexdigest(),
                            "variables": ["cost"],
                            "evidence": {
                                "d": 2,
                                "k": 1,
                                "cost": 5.5,
                                "sample_count": 500,
                            },
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        (root / "results/summary.csv").write_text(
            "d,k,gamma,status,method,solver,sample_count,certificate,artifact\n"
            "2,1,5.5,validated,exact,sdpt3,500,baseline,results/certified/example.mat\n",
            encoding="utf-8",
        )
        for name in ("run_exact_k14.m", "run_exact_k56.m"):
            (root / "experiments/server/kcopy_d2" / name).write_text(
                "opts.s = 500;\nopts.certFresh = 50;\n", encoding="utf-8"
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

    def test_sensitive_path_inside_json_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_fixture(root)
            path = root / "docs/provenance/example.json"
            path.parent.mkdir(parents=True)
            path.write_text(
                json.dumps({"source": "/home/" + "alice/private-result.mat"}),
                encoding="utf-8",
            )
            self.assertIn(
                f"{Path('docs/provenance/example.json')}: contains personal home path",
                validate_repository(root),
            )

    def test_mat_manifest_hash_and_schema_contract_fail_when_tampered(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_fixture(root)
            manifest_path = root / "results/mat-artifacts.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["artifacts"][0]["current_sha256"] = "0" * 64
            manifest["artifacts"][0]["variables"] = []
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            errors = validate_repository(root)
            self.assertIn(
                "results/certified/example.mat: SHA-256 does not match mat-artifacts.json",
                errors,
            )
            self.assertIn(
                "results/certified/example.mat: artifact manifest has no variables",
                errors,
            )

    def test_validated_summary_row_rejects_diagnostic_mat(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_fixture(root)
            manifest_path = root / "results/mat-artifacts.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["artifacts"][0]["classification"] = "diagnostic"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            self.assertIn(
                "results/summary.csv:2: validated row references diagnostic MAT artifact",
                validate_repository(root),
            )

    def test_mat_manifest_rejects_path_outside_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repository"
            self.make_fixture(root)
            outside = Path(tmp) / "outside.mat"
            outside.write_bytes(b"MAT")
            manifest_path = root / "results/mat-artifacts.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["artifacts"][0]["path"] = "../outside.mat"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            self.assertIn(
                "results/mat-artifacts.json: invalid artifact path ../outside.mat",
                validate_repository(root),
            )

    def test_invalid_summary_columns_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_fixture(root)
            (root / "results/summary.csv").write_text(
                "d,k,gamma,status\n2,1,5.5,validated\n", encoding="utf-8"
            )
            self.assertIn(
                "results/summary.csv: invalid summary columns",
                validate_repository(root),
            )

    def test_invalid_summary_status_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_fixture(root)
            summary = root / "results/summary.csv"
            summary.write_text(
                summary.read_text(encoding="utf-8").replace(
                    "validated", "unverified"
                ),
                encoding="utf-8",
            )
            self.assertIn(
                "results/summary.csv:2: invalid status 'unverified'",
                validate_repository(root),
            )

    def test_missing_summary_artifact_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_fixture(root)
            summary = root / "results/summary.csv"
            summary.write_text(
                summary.read_text(encoding="utf-8").replace(
                    "results/certified/example.mat", "results/certified/missing.mat"
                ),
                encoding="utf-8",
            )
            self.assertIn(
                "results/summary.csv:2: missing artifact results/certified/missing.mat",
                validate_repository(root),
            )

    def test_later_sample_count_override_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_fixture(root)
            runner = root / "experiments/server/kcopy_d2/run_exact_k14.m"
            runner.write_text("opts.s = 500;\nopts.s = 1;\n", encoding="utf-8")
            self.assertIn(
                "experiments/server/kcopy_d2/run_exact_k14.m: opts.s is below 500",
                validate_repository(root),
            )

    def test_sample_count_of_600_without_500_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_fixture(root)
            runner = root / "experiments/server/kcopy_d2/run_exact_k14.m"
            runner.write_text("opts.s = 600;\n", encoding="utf-8")
            self.assertIn(
                "experiments/server/kcopy_d2/run_exact_k14.m: missing opts.s = 500",
                validate_repository(root),
            )

    def test_missing_cert_fresh_of_50_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_fixture(root)
            runner = root / "experiments/server/kcopy_d2/run_exact_k14.m"
            runner.write_text("opts.s = 500;\n", encoding="utf-8")
            self.assertIn(
                "experiments/server/kcopy_d2/run_exact_k14.m: missing opts.certFresh = 50",
                validate_repository(root),
            )

    def test_later_cert_fresh_override_below_50_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_fixture(root)
            runner = root / "experiments/server/kcopy_d2/run_exact_k14.m"
            runner.write_text(
                "opts.s = 500;\nopts.certFresh = 50;\nopts.certFresh = 49;\n",
                encoding="utf-8",
            )
            self.assertIn(
                "experiments/server/kcopy_d2/run_exact_k14.m: opts.certFresh is below 50",
                validate_repository(root),
            )

    def test_nested_expression_linear_call_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_fixture(root)
            runner = root / "experiments/server/kcopy_d2/run_exact_k14.m"
            runner.write_text(
                "opts.s = 500;\n"
                "result = gamma_k_d2(build_input(alpha(beta)), ...\n"
                "    'linear', opts);\n",
                encoding="utf-8",
            )
            self.assertIn(
                "experiments/server/kcopy_d2/run_exact_k14.m: exact runner invokes gamma_k_d2 linear mode",
                validate_repository(root),
            )

    def test_generic_sensitive_markers_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_fixture(root)
            path = root / "README.md"
            path.write_text(
                "/home/" + "alice/project\n" + "192." + "168.1.15\n",
                encoding="utf-8",
            )
            errors = validate_repository(root)
            self.assertIn("README.md: contains personal home path", errors)
            self.assertIn("README.md: contains IP address", errors)
            path.write_text(
                "-" * 5 + "BEGIN PRIVATE KEY" + "-" * 5 + "\n",
                encoding="utf-8",
            )
            self.assertIn(
                "README.md: contains private-key marker", validate_repository(root)
            )

    def test_workspace_staging_is_excluded_and_placeholder_home_path_is_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_fixture(root)
            (root / "docs/experiment-manifest.md").write_text(
                "/home/<user>/project\n", encoding="utf-8"
            )
            staging = root / ".workspace/staging"
            staging.mkdir(parents=True)
            (staging / "notes.md").write_text(
                "/home/" + "alice/matlab_codes\n" + "10.4." + "6.4\n"
                + "-" * 5 + "BEGIN RSA PRIVATE KEY" + "-" * 5 + "\n",
                encoding="utf-8",
            )
            self.assertEqual(validate_repository(root), [])

    def test_workspace_policy_file_is_scanned(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_fixture(root)
            policy = root / ".workspace/policy.md"
            policy.parent.mkdir(parents=True)
            policy.write_text("/ho" + "me/alice/matlab_codes\n", encoding="utf-8")
            self.assertIn(
                f"{Path('.workspace') / 'policy.md'}: contains personal home path",
                validate_repository(root),
            )

    def test_linear_relaxation_requires_clear_legacy_labeling(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.make_fixture(root)
            legacy = root / "legacy/README.md"
            legacy.write_text("This documents the legacy linear relaxation.\n", encoding="utf-8")
            errors = validate_repository(root)
            self.assertIn(
                "legacy: linear-relaxation documentation must state lower-bound and not-equivalent wording",
                errors,
            )
            legacy.write_text(
                "This legacy linear relaxation is a lower-bound result and is not equivalent to the exact result.\n",
                encoding="utf-8",
            )
            self.assertEqual(validate_repository(root), [])


if __name__ == "__main__":
    unittest.main()
