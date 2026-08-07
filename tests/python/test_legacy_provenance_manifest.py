"""Integrity checks for Task 5 historical-source provenance."""

import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs" / "provenance" / "legacy-task-5-manifest.json"
SOURCE_COMMIT = "45127901a920384c3f4ec56f0ecfe15b78028d0a"
RECORDED_SOURCE_SHA256 = "bb6cfb31d3bf926ed9059a31d14893aaea5e75ebadda0355df67f9be4d78bf01"
RECORDED_SOURCE_BYTE_COUNT = 1960


def lf_normalized_utf8(path):
    text = path.read_text(encoding="utf-8")
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


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
        self.assertEqual(recorded["source_provenance"], "recorded external source")
        self.assertEqual(recorded["newline_normalization"], "LF-normalized UTF-8 text")
        self.assertEqual(recorded["recorded_source_sha256"], RECORDED_SOURCE_SHA256)
        self.assertEqual(recorded["recorded_source_byte_count"], RECORDED_SOURCE_BYTE_COUNT)

        destination = ROOT / recorded["destination_path"]
        digest = hashlib.sha256(lf_normalized_utf8(destination)).hexdigest()
        self.assertEqual(digest, recorded["destination_sha256"])


if __name__ == "__main__":
    unittest.main()
