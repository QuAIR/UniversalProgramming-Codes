"""Source-level checks for the supported SDP implementation."""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[2]


class SupportedSourceTest(unittest.TestCase):
    def test_supported_source_layout_and_solver_defaults(self):
        expected_files = (
            "src/matlab/common/build_walled_brauer.m",
            "src/matlab/common/decompose_brauer_algebra.m",
            "src/matlab/common/decompose_sector.m",
            "src/matlab/common/random_SU.m",
            "src/matlab/kcopy_d2/gamma_k_d2_exact.m",
            "src/matlab/up_config.m",
            "src/matlab/up_setup.m",
            "src/python/irrep_dimensions.py",
            "src/python/sk_invariance_reduction.py",
        )
        for relative in expected_files:
            self.assertTrue((ROOT / relative).is_file(), relative)

        solver = (ROOT / "src/matlab/kcopy_d2/gamma_k_d2_exact.m").read_text(
            encoding="ascii"
        )
        self.assertIn("defaults.s = 500;", solver)
        self.assertIn("defaults.certFresh = 50;", solver)
        self.assertIn("defaults.solver = 'sdpt3';", solver)
        self.assertIn("fullfile(thisDir, '..', 'common')", solver)
        self.assertNotIn("fullfile(thisDir, '..', 'code')", solver)

    def test_general_d_baseline_is_not_supported_source(self):
        self.assertFalse((ROOT / "src/matlab/common/gamma_k.m").exists())
        self.assertFalse((ROOT / "src/matlab/kcopy_d2/gamma_k.m").exists())

    def test_portable_configuration_contract(self):
        config = (ROOT / "src/matlab/up_config.m").read_text(encoding="ascii")
        for variable in (
            "UP_CVX_ROOT",
            "UP_QETLAB_ROOT",
            "UP_YALMIP_ROOT",
            "UP_MATLAB_BIN",
            "UP_SDP_SOLVER",
            "UP_RESULTS_ROOT",
        ):
            self.assertIn(variable, config)
        self.assertIn("results', 'generated", config)

        setup = (ROOT / "src/matlab/up_setup.m").read_text(encoding="ascii")
        for identifier in (
            "up_setup:missingCVX",
            "up_setup:missingQETLAB",
            "up_setup:missingYALMIP",
        ):
            self.assertIn(identifier, setup)


if __name__ == "__main__":
    unittest.main()
