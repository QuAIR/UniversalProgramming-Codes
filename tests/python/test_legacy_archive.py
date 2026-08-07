"""Source-level checks for the retained provenance archive."""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]


class LegacyArchiveTest(unittest.TestCase):
    def read(self, relative):
        path = ROOT / relative
        self.assertTrue(path.is_file(), relative)
        return path.read_text(encoding="ascii")

    def test_archive_contains_all_task_five_sources(self):
        expected = (
            "legacy/README.md",
            "legacy/general-d-baseline/README.md",
            "legacy/general-d-baseline/gamma_k.m",
            "legacy/general-d-baseline/decompose_brauer_algebra.m",
            "legacy/general-d-baseline/generators/gen.sh",
            "legacy/general-d-baseline/generators/genfast.sh",
            "legacy/general-d-baseline/generators/genbrute.sh",
            "legacy/qubit-reduced-prototype/README.md",
            "legacy/qubit-reduced-prototype/gamma_k_d2.m",
            "legacy/qubit-reduced-prototype/run_kcopy_d2.m",
            "legacy/qubit-reduced-prototype/run_quair06_k14.m",
            "legacy/qubit-reduced-prototype/run_quair06_k14.sh",
            "legacy/qubit-reduced-prototype/launch_quair06_k14.sh",
            "legacy/linear-relaxation/README.md",
            "legacy/linear-relaxation/run_quair06_linear_k14.m",
            "legacy/linear-relaxation/run_quair06_linear_k14.sh",
            "legacy/linear-relaxation/launch_quair06_linear_k14.sh",
            "legacy/failed-runs/README.md",
            "legacy/failed-runs/fixed_protocol_cost_check.m",
        )
        for relative in expected:
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_legacy_warnings_preserve_defect_and_relaxation_status(self):
        archive = self.read("legacy/README.md").lower()
        baseline = self.read("legacy/general-d-baseline/README.md").lower()
        prototype = self.read("legacy/qubit-reduced-prototype/README.md").lower()
        relaxation = self.read("legacy/linear-relaxation/README.md").lower()
        failed = self.read("legacy/failed-runs/README.md").lower()

        self.assertIn("permutesystems", archive)
        self.assertIn("k>=3", baseline)
        self.assertIn("not a supported entry point", baseline)
        self.assertIn("full raw-row mode", prototype)
        self.assertIn("m=0,1", prototype)
        for documentation in (archive, prototype, relaxation):
            normalized = " ".join(documentation.split())
            self.assertIn("lower bound", normalized)
            self.assertIn("not equivalent", normalized)
            self.assertIn("below the exact optimum", normalized)
            self.assertIn("must not be cited as gamma_k", normalized)
        self.assertIn("under-sampled", failed)
        self.assertIn("provenance", failed)

    def test_portable_wrappers_use_repo_relative_or_environment_paths(self):
        wrappers = (
            "legacy/general-d-baseline/generators/gen.sh",
            "legacy/general-d-baseline/generators/genfast.sh",
            "legacy/general-d-baseline/generators/genbrute.sh",
            "legacy/qubit-reduced-prototype/run_quair06_k14.sh",
            "legacy/qubit-reduced-prototype/launch_quair06_k14.sh",
            "legacy/linear-relaxation/run_quair06_linear_k14.sh",
            "legacy/linear-relaxation/launch_quair06_linear_k14.sh",
        )
        for relative in wrappers:
            source = self.read(relative)
            self.assertNotRegex(source, r"/home/|/Users/|10\.4\.6\.", relative)
        self.assertIn("UP_QETLAB_ROOT", self.read("legacy/general-d-baseline/generators/gen.sh"))
        for relative in (wrappers[3], wrappers[5]):
            source = self.read(relative)
            self.assertIn("repo_root", source, relative)
            self.assertIn("UP_MATLAB_BIN", source, relative)
        for relative in (wrappers[4], wrappers[6]):
            source = self.read(relative)
            self.assertIn("repo_root", source, relative)
            self.assertIn("run_quair06", source, relative)

    def test_fixed_protocol_diagnostic_uses_portable_setup_and_recorded_status(self):
        source = self.read("legacy/failed-runs/fixed_protocol_cost_check.m")
        readme = self.read("legacy/failed-runs/README.md")
        self.assertRegex(source, r"^function fixed_protocol_cost_check\(\)", re.MULTILINE)
        self.assertIn("cfg = up_config();", source)
        self.assertIn("up_setup(cfg, false);", source)
        self.assertIn("for k = 1:3", source)
        self.assertIn("cvx_solver sdpt3", source)
        self.assertIn("SCHEME_COST", source)
        self.assertIn("5.500000001339", readme)
        self.assertIn("3.666666669558", readme)
        self.assertIn("MATLAB terminated during the attempted run", readme)
        self.assertNotRegex(readme.lower(), r"k=3[^\n]*cost\s*=\s*\d")

    def test_primary_source_does_not_depend_on_legacy_or_linear_solver(self):
        primary = (ROOT / "src", ROOT / "experiments")
        legacy_reference = re.compile(r"legacy(?:/|\\\\)")
        linear_call = re.compile(r"gamma_k_d2\s*\([^\n]*['\"]linear['\"]", re.IGNORECASE)
        for directory in primary:
            for path in directory.rglob("*"):
                if path.suffix not in {".m", ".py", ".sh"}:
                    continue
                source = path.read_text(encoding="ascii")
                self.assertNotRegex(source, legacy_reference, path)
                self.assertNotRegex(source, linear_call, path)


if __name__ == "__main__":
    unittest.main()
