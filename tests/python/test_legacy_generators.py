"""Executable checks for the historical general-d generator wrappers."""

from pathlib import Path
import os
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
GENERATORS = ROOT / "legacy" / "general-d-baseline" / "generators"
BASH = shutil.which("bash")


@unittest.skipUnless(BASH, "bash is required to exercise the generator wrappers")
class LegacyGeneratorTest(unittest.TestCase):
    def run_generator(self, name, *arguments, output_root=None):
        environment = os.environ.copy()
        environment.pop("UP_REPO_ROOT", None)
        if output_root is not None:
            environment["UP_RESULTS_ROOT"] = str(output_root)
        return subprocess.run(
            [BASH, str(GENERATORS / name), *map(str, arguments)],
            cwd=ROOT,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_gen_generates_portable_historical_pipeline_in_isolated_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            output_root = Path(temporary) / "outputs"
            result = self.run_generator("gen.sh", 2, 2, output_root=output_root)

            self.assertEqual(result.returncode, 0, result.stderr)
            generated = Path(result.stdout.strip().splitlines()[-1])
            self.assertTrue(generated.is_file(), generated)
            self.assertTrue(generated.is_relative_to(output_root))
            source = generated.read_text(encoding="ascii")

        # Parameterization and all historical transformations remain present.
        for marker in (
            "d = 2;",
            "k = 2;",
            "s = 500;",
            "method = 'hilbert';",
            "V1=zeros(Dsec^2,bl1)",
            "ipm = zeros(1,2*k+2)",
            "TPR = orth(",
            "cvx_solver mosek;",
            "ARED*(b1-b2) == BRED;",
            "(J1_blk + ctranspose(J1_blk))/2 >= 0;",
            "(J2_blk + ctranspose(J2_blk))/2 >= 0;",
        ):
            self.assertIn(marker, source)
        for removed_constraint in (
            "TP1 == p1 * eye(dim_tp);",
            "TP2 == p2 * eye(dim_tp);",
            "prog == d * JC(:,:,c);",
        ):
            self.assertNotIn(removed_constraint, source)

        # Portable setup keeps an environment override and embeds a fallback.
        self.assertIn('repo_root = getenv("UP_REPO_ROOT");', source)
        self.assertIn('if isempty(repo_root), repo_root = "', source)
        self.assertNotIn("legacy:missingRepoRoot", source)
        self.assertIn('cfg = up_config(); up_setup(cfg, false); rng(0);', source)
        self.assertIn(
            'outputDir = fullfile(cfg.resultsRoot, "legacy", "general-d-baseline");',
            source,
        )
        self.assertIn('mkdir(outputDir)', source)
        self.assertIn('save(fullfile(outputDir, sprintf("gamma_d%d_k%d_s%d_r%d.mat"', source)
        self.assertNotIn('sprintf("results/gamma_', source)

    def test_generators_reject_noninteger_and_malicious_arguments(self):
        invalid_argument_sets = (
            ("2.5", "2"),
            ("2; touch injected", "2"),
            ("2", "0"),
            ("2", "2", "0"),
            ("2", "2", "500", "-1"),
        )
        for name in ("gen.sh", "genfast.sh", "genbrute.sh"):
            for arguments in invalid_argument_sets:
                with self.subTest(generator=name, arguments=arguments):
                    result = self.run_generator(name, *arguments)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("Usage:", result.stderr)

    def test_genfast_keeps_its_historical_sparse_transformations(self):
        with tempfile.TemporaryDirectory() as temporary:
            output_root = Path(temporary) / "outputs"
            result = self.run_generator("genfast.sh", 2, 2, output_root=output_root)

            self.assertEqual(result.returncode, 0, result.stderr)
            generated = Path(result.stdout.strip().splitlines()[-1])
            self.assertTrue(generated.is_file(), generated)
            self.assertTrue(generated.is_relative_to(output_root))
            source = generated.read_text(encoding="ascii")

        for marker in (
            "kron(sparse(basis_1k{j1}), sparse(basis_k1{j2}))",
            "T(:,:,j) = full(PartialTrace(B{j}, 2*k+2, dims_all));",
            "P(:,:,j,c) = full(PartialTrace(B{j} * ins, 2, [d, dk^2, d]));",
        ):
            self.assertIn(marker, source)

    def test_genbrute_reports_missing_historical_input(self):
        with tempfile.TemporaryDirectory() as temporary:
            output_root = Path(temporary) / "outputs"
            result = self.run_generator("genbrute.sh", 2, 2, output_root=output_root)

            self.assertEqual(result.returncode, 2)
            self.assertIn("Missing historical provenance input", result.stderr)
            self.assertFalse(output_root.exists())


if __name__ == "__main__":
    unittest.main()
