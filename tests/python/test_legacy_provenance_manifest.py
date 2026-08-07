"""Integrity checks for Task 5 historical-source provenance."""

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs" / "provenance" / "legacy-task-5-manifest.json"
SOURCE_COMMIT = "45127901a920384c3f4ec56f0ecfe15b78028d0a"


class LegacyProvenanceManifestTest(unittest.TestCase):
    def test_byte_identical_historical_algorithms_match_manifest_hashes(self):
        manifest = json.loads(MANIFEST.read_text(encoding="ascii"))
        self.assertEqual(manifest["source_commit"], SOURCE_COMMIT)
        algorithms = manifest["byte_identical_algorithms"]
        self.assertEqual(len(algorithms), 3)

        for entry in algorithms:
            with self.subTest(destination=entry["destination_path"]):
                destination = ROOT / entry["destination_path"]
                digest = hashlib.sha256(destination.read_bytes()).hexdigest()
                self.assertEqual(digest, entry["destination_sha256"])
                self.assertRegex(entry["source_blob_id"], r"^[0-9a-f]{40}$")

    def test_recorded_fixed_protocol_provenance_and_allowed_changes_are_declared(self):
        manifest = json.loads(MANIFEST.read_text(encoding="ascii"))
        recorded = manifest["fixed_protocol_recorded_source"]
        self.assertEqual(recorded["thread_id"], "019edee4-55ea-7eb0-8212-29e7fb828ead")
        self.assertEqual(recorded["turn_id"], "019ee427-6a19-7e61-b49c-8cb73e03db88")
        self.assertTrue(recorded["allowed_current_file_transformations"])
        self.assertTrue(manifest["allowed_current_file_transformations"])


if __name__ == "__main__":
    unittest.main()
