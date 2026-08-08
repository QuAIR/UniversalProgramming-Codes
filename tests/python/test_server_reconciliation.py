"""Checks for the read-only 2026-08-07 server reconciliation."""

import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[2]
INVENTORY = ROOT / "docs/provenance/server-live-inventory.json"
MAT_MANIFEST = ROOT / "results/mat-artifacts.json"

NEW_MATS = {
    "results/diagnostic/server_exact_d2_k5_saved_blocks.mat",
    "results/diagnostic/server_exact_k56_checkpoint.mat",
    "results/diagnostic/server_full_vs_linear_k1_k3.mat",
    "results/diagnostic/server_struct2_d3_k1.mat",
    "results/diagnostic/server_struct2_d3_k2.mat",
    "results/diagnostic/server_struct3_d4_k1.mat",
    "results/diagnostic/server_struct3_d4_k2.mat",
    "results/diagnostic/server_y3_d4_k3.mat",
    "results/diagnostic/server_y3_d5_k2.mat",
    "results/diagnostic/server_yalmip_d3_k2.mat",
}


class ServerReconciliationTest(unittest.TestCase):
    @staticmethod
    def _inventory():
        return json.loads(INVENTORY.read_text(encoding="utf-8"))

    @staticmethod
    def _mat_manifest():
        return json.loads(MAT_MANIFEST.read_text(encoding="utf-8"))

    def test_inventory_covers_the_two_verified_live_roots(self):
        inventory = self._inventory()
        self.assertEqual(inventory["schema_version"], 2)
        self.assertEqual(inventory["reconciliation_date"], "2026-08-07")
        self.assertEqual(inventory["mtime_capture_date"], "2026-08-08")
        self.assertEqual(inventory["file_count"], 205)
        self.assertEqual(inventory["roots"], {"qubit": 57, "general-d": 148})
        self.assertEqual(inventory["live_hash_mismatches"], 0)
        self.assertTrue(inventory["read_only"])
        self.assertFalse(inventory["job_running_or_started"])
        self.assertIn("captured directly", inventory["remote_mtime_note"].lower())
        entries = inventory["files"]
        self.assertEqual(len(entries), 205)
        keys = {(entry["source_root"], entry["relative_path"]) for entry in entries}
        self.assertEqual(len(keys), 205)
        for entry in entries:
            self.assertRegex(entry["source_sha256"], r"^[0-9a-f]{64}$")
            self.assertGreaterEqual(entry["bytes"], 0)
            modified = datetime.fromisoformat(
                entry["source_mtime_utc"].replace("Z", "+00:00")
            )
            self.assertEqual(modified.tzinfo, timezone.utc)
            self.assertIn("disposition", entry)
            self.assertIn("reason", entry)
            target = entry.get("local_target")
            if target:
                self.assertTrue((ROOT / target).is_file(), target)

    def test_every_remote_source_is_mapped_or_archived_and_hashed(self):
        source_entries = [
            entry
            for entry in self._inventory()["files"]
            if Path(entry["relative_path"]).suffix.lower() in {".m", ".py", ".sh"}
        ]
        self.assertEqual(len(source_entries), 95)
        for entry in source_entries:
            self.assertIn(
                entry["disposition"],
                {"mapped_portable", "archived_exact", "archived_sanitized"},
            )
            self.assertIn("source_status", entry)
            target = ROOT / entry["local_target"]
            self.assertTrue(target.is_file(), entry)
            self.assertEqual(
                hashlib.sha256(target.read_bytes()).hexdigest(),
                entry["current_sha256"],
                entry,
            )

    def test_archives_are_bom_free_and_transformations_are_explicit(self):
        attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
        self.assertIn(
            "legacy/server-snapshots/server-2026-08-07/** text eol=lf",
            attributes,
        )
        archived = [
            entry
            for entry in self._inventory()["files"]
            if entry["disposition"] in {"archived_exact", "archived_sanitized"}
        ]
        self.assertEqual(len(archived), 57)
        self.assertEqual(
            sum(entry["disposition"] == "archived_exact" for entry in archived),
            5,
        )
        self.assertEqual(
            sum(entry["disposition"] == "archived_sanitized" for entry in archived),
            52,
        )
        allowed = {
            "host_path_neutralized",
            "pbt_local_import_path",
            "trailing_whitespace_removed",
        }
        for entry in archived:
            transformations = entry.get("transformations")
            self.assertIsInstance(transformations, list, entry)
            self.assertTrue(set(transformations) <= allowed, entry)
            content = (ROOT / entry["local_target"]).read_bytes()
            self.assertFalse(content.startswith(b"\xef\xbb\xbf"), entry)
            if entry["disposition"] == "archived_exact":
                self.assertEqual(transformations, [], entry)
                self.assertEqual(entry["current_sha256"], entry["source_sha256"])
                self.assertEqual(len(content), entry["bytes"])
            else:
                self.assertTrue(transformations, entry)

    def test_mat_manifest_covers_the_ten_live_only_evidence_files(self):
        manifest = self._mat_manifest()
        self.assertEqual(manifest["artifact_count"], 44)
        self.assertEqual(manifest["live_reconciliation"]["source_file_count"], 205)
        self.assertEqual(manifest["live_reconciliation"]["sdp_solves"], 0)
        entries = {entry["path"]: entry for entry in manifest["artifacts"]}
        self.assertTrue(NEW_MATS <= entries.keys())
        for path in NEW_MATS:
            entry = entries[path]
            self.assertEqual(entry["classification"], "diagnostic")
            self.assertEqual(entry["source"]["snapshot_date"], "2026-08-07")
            self.assertEqual(
                hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
                entry["current_sha256"],
            )

    def test_exact_k56_log_is_compact_and_k6_is_not_claimed_solved(self):
        path = ROOT / "results/logs/server_exact_k56_checkpoint.csv"
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual({row["k"] for row in rows}, {"5", "6"})
        k5 = next(row for row in rows if row["k"] == "5")
        k6 = next(row for row in rows if row["k"] == "6")
        self.assertEqual(k5["status"], "diagnostic_numerical_candidate")
        self.assertEqual(k5["warning"], "linsysolve_nan_or_inf")
        self.assertEqual(k6["status"], "incomplete")
        self.assertEqual(k6["cost"], "NaN")
        log = (ROOT / "results/logs/server_exact_k56_checkpoint.log").read_text(
            encoding="utf-8"
        )
        self.assertIn("warning=linsysolve_nan_or_inf", log)
        self.assertIn("all_cptp_feasibility_certified=false", log)
        self.assertIn("k=6 status=incomplete", log)
        self.assertIn("solve_completed=false", log)
        self.assertNotIn("/home/", log)

        entry = next(
            item
            for item in self._mat_manifest()["artifacts"]
            if item["path"]
            == "results/diagnostic/server_exact_d2_k5_saved_blocks.mat"
        )
        self.assertEqual(entry["diagnostic_type"], "numerical_candidate")
        self.assertEqual(
            entry["evidence"]["classification_status"],
            "diagnostic_numerical_candidate",
        )

    def test_canonical_d2_k5_value_is_unchanged(self):
        with (ROOT / "results/summary.csv").open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        row = next(row for row in rows if row["d"] == "2" and row["k"] == "5")
        self.assertEqual(row["gamma"], "1.350907")
        self.assertEqual(row["artifact"], "results/certified/general_d/struct2_d2_k5.mat")

    def test_pbt_snapshot_is_explicitly_historical(self):
        readme = ROOT / "legacy/server-snapshots/server-2026-08-07/README.md"
        text = readme.read_text(encoding="utf-8")
        self.assertIn("recovered claim", text)
        self.assertIn("not independently re-proven", text)
        self.assertTrue(
            (ROOT / "legacy/server-snapshots/server-2026-08-07/general-d/pbt_bound/pbt_bound.py").is_file()
        )

    def test_matlab_loads_k5_blocks_and_incomplete_k6_without_solving(self):
        matlab = os.environ.get("MATLAB_EXE") or shutil.which("matlab")
        if matlab is None:
            conventional = Path("D:/MATLAB/bin/matlab.exe")
            matlab = str(conventional) if conventional.is_file() else None
        if matlab is None:
            self.skipTest("MATLAB is unavailable")
        script = (ROOT / "tests/matlab/test_server_evidence.m").as_posix()
        result = subprocess.run(
            [matlab, "-batch", f"run('{script}')"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            timeout=300,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_no_internal_workspace_files_are_tracked(self):
        tracked = subprocess.run(
            ["git", "ls-files", ".workspace"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.splitlines()
        self.assertEqual(tracked, [])


if __name__ == "__main__":
    unittest.main()
