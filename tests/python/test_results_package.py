"""Integration checks for the curated historical results package."""

import csv
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "results/mat-artifacts.json"

CERTIFIED_GENERAL_D = {
    "cert_d2_k3.mat",
    "cert_d2_k4.mat",
    "cert_d4_k2.mat",
    "cert_d5_k2.mat",
    "struct2_d2_k5.mat",
    "struct2_d3_k3.mat",
    "struct3_d4_k3.mat",
    "y3_d4_k4.mat",
    "y3_d5_k3.mat",
}
EXACT_D2 = {f"exact_d2_k{k}.mat" for k in range(1, 5)}
DIAGNOSTIC_MATS = {
    "historical_kcopy_d2_quair06_exact_k14.mat",
    "historical_kcopy_d2_quair06_linear_k14.mat",
    "historical_results_brute_d2_k1_s500_r0.mat",
    "historical_results_brute_d2_k3_s300_r0.mat",
    "historical_results_gamma_d2_k1_s500_r0.mat",
    "historical_results_gamma_d2_k2.mat",
    "historical_results_gamma_d2_k2_fix.mat",
    "historical_results_gamma_d2_k2_s500_r0.mat",
    "historical_results_gamma_d2_k2_s500_r7.mat",
    "historical_results_gamma_d2_k3_s500_r0.mat",
    "historical_results_gamma_d2_k4_s500_r0.mat",
    "historical_results_gamma_d3_k1_s500_r0.mat",
    "historical_results_gamma_d3_k2_fix.mat",
    "historical_results_gamma_d3_k2_s500_r0.mat",
    "historical_results_gamma_d3_k2_s800_r1.mat",
    "historical_results_struct2_d2_k3.mat",
    "historical_results_struct2_d2_k4.mat",
    "historical_results_struct_d2_k3.mat",
    "historical_results_struct_d2_k4.mat",
    "historical_results_yalmip_d2_k3.mat",
    "historical_results_yalmip_d2_k4.mat",
    "quair06_exact_d2_k5_saved_blocks.mat",
    "quair06_exact_k56_checkpoint.mat",
    "quair06_full_vs_linear_k1_k3.mat",
    "quair06_struct2_d3_k1.mat",
    "quair06_struct2_d3_k2.mat",
    "quair06_struct3_d4_k1.mat",
    "quair06_struct3_d4_k2.mat",
    "quair06_y3_d4_k3.mat",
    "quair06_y3_d5_k2.mat",
    "quair06_yalmip_d3_k2.mat",
}
EXPECTED_COSTS = {
    (2, 1): "5.500000", (2, 2): "2.713330", (2, 3): "1.888291",
    (2, 4): "1.529423", (2, 5): "1.350907", (3, 1): "15.222222",
    (3, 2): "7.456450", (3, 3): "4.882170", (3, 4): "3.619643",
    (4, 1): "29.125000", (4, 2): "14.366215", (4, 3): "9.453850",
    (4, 4): "7.003853", (5, 1): "47.080000", (5, 2): "23.324402",
    (5, 3): "15.410364",
}
EXPECTED_FIGURE_NU = {
    (2, 1): "5.5000", (2, 2): "2.7133", (2, 3): "1.8883",
    (2, 4): "1.5294", (2, 5): "1.3509", (3, 1): "15.222",
    (3, 2): "7.4565", (3, 3): "4.8822", (3, 4): "3.6197",
    (4, 1): "29.125", (4, 2): "14.3662", (4, 3): "9.4538",
    (4, 4): "7.0039", (5, 1): "47.080", (5, 2): "23.3244",
    (5, 3): "15.4104",
}


class ResultsPackageTest(unittest.TestCase):
    @staticmethod
    def _manifest():
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    def test_curated_mat_inventory_is_complete_and_excludes_partials(self):
        actual = {
            path.relative_to(ROOT / "results").as_posix()
            for path in (ROOT / "results").rglob("*.mat")
        }
        expected = (
            {f"certified/general_d/{name}" for name in CERTIFIED_GENERAL_D}
            | {f"certified/kcopy_d2/{name}" for name in EXACT_D2}
            | {f"diagnostic/{name}" for name in DIAGNOSTIC_MATS}
        )
        self.assertEqual(actual, expected)
        self.assertEqual(len(CERTIFIED_GENERAL_D) + len(EXACT_D2), 13)
        self.assertEqual(len(DIAGNOSTIC_MATS), 31)
        tracked = subprocess.run(
            ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout.splitlines()
        self.assertFalse([path for path in tracked if path.endswith("_partial.mat")])
        self.assertFalse([path for path in tracked if path.endswith("_partial.csv")])

    def test_summary_rows_have_canonical_costs_and_existing_evidence(self):
        with (ROOT / "results/summary.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        actual = {(int(row["d"]), int(row["k"])): row for row in rows}
        self.assertEqual(set(actual), set(EXPECTED_COSTS))
        for key, gamma in EXPECTED_COSTS.items():
            self.assertEqual(actual[key]["gamma"], gamma, key)
            artifact = actual[key]["artifact"]
            if key == (2, 1):
                self.assertEqual(
                    artifact, "results/certified/kcopy_d2/exact_d2_k1.mat"
                )
                self.assertTrue((ROOT / artifact).is_file(), (key, artifact))
            elif key[1] == 1:
                self.assertEqual(artifact, "", key)
            else:
                self.assertTrue((ROOT / artifact).is_file(), (key, artifact))
        self.assertEqual(actual[(3, 4)]["status"], "diagnostic")
        self.assertEqual(
            actual[(2, 2)]["artifact"], "results/certified/kcopy_d2/exact_d2_k2.mat"
        )
        self.assertEqual(
            actual[(3, 4)]["artifact"],
            "legacy/failed-runs/logs/y_d3k4_postsolve_terminated.log",
        )
        self.assertEqual(actual[(2, 3)]["method"], "full_space_certified_sdp")
        self.assertEqual(actual[(2, 3)]["solver"], "cvx-mosek")
        self.assertEqual(actual[(2, 4)]["method"], "full_space_certified_sdp")
        self.assertEqual(actual[(2, 4)]["solver"], "cvx-mosek")

    def test_manifest_covers_and_hashes_every_mat_artifact(self):
        manifest = self._manifest()
        self.assertEqual(manifest["schema_version"], 1)
        self.assertEqual(manifest["source_commit"], "4512790")
        artifacts = manifest["artifacts"]
        self.assertEqual(manifest["artifact_count"], 44)
        self.assertEqual(len(artifacts), 44)
        by_path = {entry["path"]: entry for entry in artifacts}
        self.assertEqual(len(by_path), len(artifacts))
        tracked_mats = {
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / "results").rglob("*.mat")
        }
        self.assertEqual(set(by_path), tracked_mats)
        for relative_path, entry in by_path.items():
            path = ROOT / relative_path
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(entry["current_sha256"], digest, relative_path)
            source = entry["source"]
            self.assertRegex(entry["source"]["sha256"], r"^[0-9a-f]{64}$")
            if source.get("snapshot_date") == "2026-08-07":
                self.assertIn(source["source_root"], {"primary", "pqga-full"})
                self.assertNotIn("git_blob_sha1", source)
                self.assertTrue(source["live_hash_verified"])
            else:
                self.assertTrue(source["path"].startswith("research_code/results/"))
                self.assertRegex(source["git_blob_sha1"], r"^[0-9a-f]{40}$")
            self.assertTrue(entry["variables"], relative_path)
            self.assertEqual(entry["variables"], sorted(entry["variables"], key=str.casefold))
            self.assertIn(entry["classification"], {"certified", "diagnostic"})
            if entry["classification"] == "certified":
                self.assertTrue(entry["checks"], relative_path)
                self.assertTrue(entry["residuals"], relative_path)

    def test_summary_mat_rows_link_to_manifest_values(self):
        by_path = {entry["path"]: entry for entry in self._manifest()["artifacts"]}
        with (ROOT / "results/summary.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        for row in rows:
            artifact = row["artifact"]
            if not artifact.endswith(".mat"):
                continue
            self.assertIn(artifact, by_path)
            evidence = by_path[artifact]["evidence"]
            self.assertEqual(evidence["d"], int(row["d"]), artifact)
            self.assertEqual(evidence["k"], int(row["k"]), artifact)
            self.assertAlmostEqual(evidence["cost"], float(row["gamma"]), places=5)
            self.assertEqual(evidence["sample_count"], int(row["sample_count"]))
            self.assertIn("status", evidence)

    def test_postsolve_termination_and_brute_cross_check_are_explicit(self):
        failed_logs = ROOT / "legacy/failed-runs/logs"
        for name in (
            "y_d3k4_postsolve_terminated.log",
            "struct2_d3k4_postsolve_terminated.log",
        ):
            content = (failed_logs / name).read_text(encoding="utf-8")
            self.assertIn("wrapper_exit_code=143", content)
            self.assertIn("objective_completed=true", content)
            self.assertIn("certificate_not_completed=true", content)
        self.assertFalse((ROOT / "results/logs/y_d3k4.log").exists())
        self.assertFalse((ROOT / "results/logs/struct2_d3k4.log").exists())
        brute = (ROOT / "results/logs/brute_d2_k2.log").read_text(encoding="utf-8")
        self.assertEqual(
            brute.splitlines(),
            [
                "brute gamma_2(CPTP, d=2), D=64",
                "RESULT brute gamma_2(CPTP, 2) = 2.713331 [Solved]",
            ],
        )
        readme = (ROOT / "results/README.md").read_text(encoding="utf-8")
        self.assertIn("results/logs/brute_d2_k2.log", readme)

    def test_exact_aggregate_records_documented_path_sanitization(self):
        target = "results/diagnostic/historical_kcopy_d2_quair06_exact_k14.mat"
        entry = next(
            item for item in self._manifest()["artifacts"] if item["path"] == target
        )
        sanitization = entry["sanitization"]
        self.assertEqual(
            sanitization["reported_source_sha256"],
            "7c6a54ad675fe91986516cebe9edb37f0023250e19052eecb8df0f6241ae3e3",
        )
        self.assertEqual(
            sanitization["source_sha256"],
            "7c6a54ad675fe91986516cebe9edb37f0023250e19052eecb8df0cab3dff2002",
        )
        self.assertFalse(sanitization["reported_hash_matches_source"])
        self.assertEqual(
            sorted(sanitization["changed_fields"]),
            ["opts.cvxRoot", "opts.helperPath", "opts.qetlabPath", "opts.resultsDir"],
        )
        for replacement in sanitization["replacements"].values():
            self.assertTrue(replacement.startswith("<"))

    def test_no_personal_paths_remain_in_tracked_bytes_or_mat_values(self):
        tracked = subprocess.run(
            ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            cwd=ROOT,
            capture_output=True,
            check=True,
        ).stdout.split(b"\0")
        forbidden = (b"/home/", b"C:\\Users\\")
        for raw_path in filter(None, tracked):
            path = ROOT / os.fsdecode(raw_path)
            if not path.is_file():
                continue
            content = path.read_bytes()
            self.assertFalse(any(token in content for token in forbidden), raw_path)

    def test_mat_schema_notes_distinguish_exact_and_historical_records(self):
        readme = (ROOT / "results/README.md").read_text(encoding="utf-8")
        self.assertIn("b1, b2, cost, info, p1, p2", readme)
        self.assertIn("does not contain saved block matrices", readme)
        self.assertIn("cost, d, k, s, cvx_status", readme)
        self.assertIn("T table and opts struct", readme)

    def test_retained_logs_are_sanitized_and_cover_nonstandard_sampling(self):
        logs = list((ROOT / "results/logs").glob("*.log"))
        self.assertTrue(logs)
        forbidden = ("/home/", "\\\\Users\\\\", "Username:", "cvxr.com/cvx/academic")
        for path in logs + list((ROOT / "legacy/failed-runs/logs").glob("*.log")):
            content = path.read_text(encoding="utf-8")
            self.assertFalse(any(token in content for token in forbidden), path)
        y3_d4 = (ROOT / "results/logs/y3_d4k4.log").read_text(encoding="utf-8")
        y3_d5 = (ROOT / "results/logs/y3_d5k3.log").read_text(encoding="utf-8")
        self.assertIn("sample_count=128", y3_d4)
        self.assertIn("sample_count=256", y3_d5)

    def test_certified_mat_schemas_values_and_residuals_load_in_matlab(self):
        matlab = os.environ.get("MATLAB_EXE") or shutil.which("matlab")
        if matlab is None:
            conventional = Path("D:/MATLAB/bin/matlab.exe")
            matlab = str(conventional) if conventional.is_file() else None
        if matlab is None:
            self.skipTest("MATLAB is unavailable")
        script = (ROOT / "tests/matlab/test_result_artifacts.m").as_posix()
        result = subprocess.run(
            [matlab, "-batch", f"run('{script}')"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=300,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_figure_script_reproduces_the_csv_points_in_a_temporary_output_dir(self):
        data = ROOT / "figures/fig3_kcopy_decay_data.csv"
        with data.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), len(EXPECTED_COSTS))
        self.assertEqual(
            {(int(row["d"]), int(row["k"])) for row in rows}, set(EXPECTED_COSTS)
        )
        self.assertEqual(
            {(int(row["d"]), int(row["k"])): row["nu"] for row in rows},
            EXPECTED_FIGURE_NU,
        )
        if importlib.util.find_spec("matplotlib") is None:
            self.skipTest("matplotlib is not available in the configured Python runtime")
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "generated"
            result = subprocess.run(
                [sys.executable, "figures/make_fig3_kcopy_decay.py"],
                cwd=ROOT,
                env={**__import__("os").environ, "FIGURES_OUTPUT_DIR": str(output_dir)},
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((output_dir / "fig3_kcopy_decay.png").is_file())


if __name__ == "__main__":
    unittest.main()
