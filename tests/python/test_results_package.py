"""Integration checks for the curated historical results package."""

import csv
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]

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
        self.assertEqual(len(DIAGNOSTIC_MATS), 21)
        self.assertFalse(list(ROOT.rglob("*_partial.mat")))
        self.assertFalse(list(ROOT.rglob("*_partial.csv")))

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
            actual[(3, 4)]["artifact"], "results/logs/y_d3k4.log"
        )

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
