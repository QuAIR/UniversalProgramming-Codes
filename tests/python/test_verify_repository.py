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
            "experiments/quair06/kcopy_d2/run_exact_k14.m",
            "experiments/quair06/kcopy_d2/run_exact_k56.m",
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
        (root / "results/summary.csv").write_text(
            "d,k,gamma,status,method,solver,sample_count,certificate,artifact\n"
            "2,1,5.5,validated,exact,sdpt3,500,baseline,results/certified/example.mat\n",
            encoding="utf-8",
        )
        for name in ("run_exact_k14.m", "run_exact_k56.m"):
            (root / "experiments/quair06/kcopy_d2" / name).write_text(
                "opts.s = 500;\n", encoding="utf-8"
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


if __name__ == "__main__":
    unittest.main()
