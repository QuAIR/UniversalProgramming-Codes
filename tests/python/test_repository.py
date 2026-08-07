"""Source-level checks for the supported SDP implementation."""

from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]


class SupportedSourceTest(unittest.TestCase):
    GENERAL_D_ENTRY_POINTS = {
        "experiments/quair06/general_d/cert_d2_k3.m": (False, 3),
        "experiments/quair06/general_d/cert_d2_k4.m": (False, 3),
        "experiments/quair06/general_d/cert_d4_k2.m": (False, 3),
        "experiments/quair06/general_d/cert_d5_k2.m": (False, 3),
        "experiments/quair06/general_d/gamma_struct3.m": (False, 3),
        "experiments/quair06/general_d/gamma_y3.m": (True, 3),
        "experiments/quair06/general_d/validate_fastP.m": (False, 3),
        "experiments/quair06/general_d/diagnostics/gamma_struct.m": (False, 4),
        "experiments/quair06/general_d/diagnostics/gamma_struct2.m": (False, 4),
        "experiments/quair06/general_d/diagnostics/gamma_y.m": (True, 4),
        "experiments/quair06/general_d/diagnostics/probe_d4k4.m": (False, 4),
    }

    def _read_general_d(self, relative):
        path = ROOT / relative
        self.assertTrue(path.is_file(), relative)
        return path.read_text(encoding="ascii")

    def _assert_entry_point_setup(self, relative, source, requires_yalmip, levels):
        root_call = "fileparts(" * levels + "scriptDir" + ")" * levels
        root_pattern = (
            rf"(?m)^[ \t]*repoRoot[ \t]*=[ \t]*"
            rf"{re.escape(root_call)};[ \t]*$"
        )
        self.assertRegex(source, root_pattern, relative)
        self.assertRegex(
            source,
            r"(?m)^[ \t]*addpath[ \t]*\([ \t]*fullfile\(repoRoot[ \t]*,[ \t]*[\"']src[\"'][ \t]*,[ \t]*[\"']matlab[\"']\)[ \t]*\);[ \t]*$",
            relative,
        )
        self.assertRegex(
            source,
            r"(?m)^[ \t]*cfg[ \t]*=[ \t]*up_config\(\);[ \t]*$",
            relative,
        )
        setup_matches = re.findall(
            r"(?m)^[ \t]*up_setup[ \t]*\([ \t]*cfg[ \t]*,[ \t]*(true|false)[ \t]*\)[ \t]*;[ \t]*$",
            source,
        )
        self.assertEqual(setup_matches, ["true" if requires_yalmip else "false"], relative)
        self.assertNotIn("/usr/local/", source, relative)

    def _save_calls(self, source):
        return re.findall(
            r"(?m)^[ \t]*save[ \t]*\(([^\r\n]*)\)[ \t]*;?[ \t]*$", source
        )

    def _assert_mat_output_contract(self, relative, source, segment, output_pattern):
        output_dir_pattern = (
            rf"(?m)^[ \t]*outputDir[ \t]*=[ \t]*fullfile\(cfg\.resultsRoot[ \t]*,[ \t]*"
            rf"[\"']quair06[\"'][ \t]*,[ \t]*[\"']general_d[\"'][ \t]*,[ \t]*[\"']{segment}[\"']\);[ \t]*$"
        )
        self.assertRegex(source, output_dir_pattern, relative)
        self.assertRegex(
            source,
            r"(?m)^[ \t]*if exist\(outputDir, [\"']dir[\"']\) ~= 7;[ \t]*mkdir\(outputDir\);[ \t]*end[ \t]*$",
            relative,
        )
        self.assertNotRegex(
            source,
            r"save[ \t]*\([^\r\n;]*[\"'][^\r\n\"']*results/",
            relative,
        )
        save_calls = self._save_calls(source)
        self.assertEqual(len(save_calls), 1, relative)
        save_args = save_calls[0]
        if output_pattern.endswith(".mat") and "%" not in output_pattern:
            self.assertRegex(
                source,
                rf"(?m)^[ \t]*outputFile[ \t]*=[ \t]*fullfile\(outputDir[ \t]*,[ \t]*[\"']{re.escape(output_pattern)}[\"']\);[ \t]*$",
                relative,
            )
            self.assertRegex(save_args, r"^[ \t]*outputFile[ \t]*,")
        else:
            self.assertRegex(
                save_args,
                rf"^[ \t]*fullfile\(outputDir[ \t]*,[ \t]*sprintf\([ \t]*[\"']{re.escape(output_pattern)}[\"'][ \t]*,[ \t]*d[ \t]*,[ \t]*k[ \t]*\)\)",
                relative,
            )

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

    def test_general_d_entry_points_have_explicit_portable_contract(self):
        outputs = {
            "experiments/quair06/general_d/cert_d2_k3.m": ("certificates", "cert_d2_k3.mat"),
            "experiments/quair06/general_d/cert_d2_k4.m": ("certificates", "cert_d2_k4.mat"),
            "experiments/quair06/general_d/cert_d4_k2.m": ("certificates", "cert_d4_k2.mat"),
            "experiments/quair06/general_d/cert_d5_k2.m": ("certificates", "cert_d5_k2.mat"),
            "experiments/quair06/general_d/gamma_struct3.m": ("validated", "struct3_d%d_k%d.mat"),
            "experiments/quair06/general_d/gamma_y3.m": ("validated", "y3_d%d_k%d.mat"),
            "experiments/quair06/general_d/diagnostics/gamma_struct.m": ("diagnostics", "struct_d%d_k%d.mat"),
            "experiments/quair06/general_d/diagnostics/gamma_struct2.m": ("diagnostics", "struct2_d%d_k%d.mat"),
            "experiments/quair06/general_d/diagnostics/gamma_y.m": ("diagnostics", "yalmip_d%d_k%d.mat"),
        }
        for relative, (requires_yalmip, levels) in self.GENERAL_D_ENTRY_POINTS.items():
            source = self._read_general_d(relative)
            self._assert_entry_point_setup(relative, source, requires_yalmip, levels)
            if relative in outputs:
                segment, output_pattern = outputs[relative]
                self._assert_mat_output_contract(relative, source, segment, output_pattern)
            else:
                self.assertNotRegex(source, r"\boutputDir\b", relative)
                self.assertEqual(self._save_calls(source), [], relative)

    def test_general_d_certificate_parameters_and_saved_variables(self):
        certificates = {
            "cert_d2_k3.m": (2, 3, 200),
            "cert_d2_k4.m": (2, 4, 200),
            "cert_d4_k2.m": (4, 2, 50),
            "cert_d5_k2.m": (5, 2, 25),
        }
        expected_variables = (
            "cost", "d", "k", "s", "b1", "b2", "p1", "p2",
            "cvx_status", "e1", "e2", "herm1", "herm2", "tpr1", "tpr2", "fres",
        )
        for name, (dimension, copies, fresh_channels) in certificates.items():
            relative = f"experiments/quair06/general_d/{name}"
            source = self._read_general_d(relative)
            self.assertEqual(re.findall(r"\bd\s*=\s*(\d+)\s*;", source), [str(dimension)], relative)
            self.assertEqual(re.findall(r"\bk\s*=\s*(\d+)\s*;", source), [str(copies)], relative)
            self.assertEqual(re.findall(r"\bs\s*=\s*(\d+)\s*;", source), ["500"], relative)
            self.assertEqual(len(re.findall(r"\brng\s*\(\s*0\s*\)\s*;", source)), 1, relative)
            self.assertRegex(source, r"\bcvx_solver\s+mosek\b", relative)
            self.assertRegex(
                source,
                rf"rng\s*\(\s*777\s*\)\s*;\s*nf\s*=\s*{fresh_channels}\s*;",
                relative,
            )
            save_args = self._save_calls(source)[0]
            variables = tuple(re.findall(r"[\"']([A-Za-z_]\w*)[\"']", save_args))
            self.assertEqual(variables, expected_variables, relative)

    def test_general_d_gamma_defaults_solver_seeds_and_outputs(self):
        gamma_scripts = {
            "experiments/quair06/general_d/gamma_struct3.m": ("validated", "struct3_d%d_k%d.mat", "cvx", 50),
            "experiments/quair06/general_d/gamma_y3.m": ("validated", "y3_d%d_k%d.mat", "yalmip", 12),
            "experiments/quair06/general_d/diagnostics/gamma_struct.m": ("diagnostics", "struct_d%d_k%d.mat", "cvx", 50),
            "experiments/quair06/general_d/diagnostics/gamma_struct2.m": ("diagnostics", "struct2_d%d_k%d.mat", "cvx", 50),
            "experiments/quair06/general_d/diagnostics/gamma_y.m": ("diagnostics", "yalmip_d%d_k%d.mat", "yalmip", 50),
        }
        for relative, (segment, output_pattern, solver, fresh_channels) in gamma_scripts.items():
            source = self._read_general_d(relative)
            self.assertEqual(re.findall(r"\bd\s*=\s*(\d+)\s*;", source), ["2"], relative)
            self.assertEqual(re.findall(r"\bk\s*=\s*(\d+)\s*;", source), ["5"], relative)
            self.assertEqual(re.findall(r"\bs\s*=\s*(\d+)\s*;", source), ["500"], relative)
            self.assertEqual(len(re.findall(r"\brng\s*\(\s*0\s*\)\s*;", source)), 1, relative)
            self.assertRegex(
                source,
                rf"rng\s*\(\s*777\s*\)\s*;\s*nf\s*=\s*{fresh_channels}\s*;",
                relative,
            )
            if solver == "cvx":
                self.assertRegex(source, r"\bcvx_solver\s+mosek\b", relative)
            else:
                self.assertRegex(
                    source,
                    r"sdpsettings\s*\([^\r\n]*[\"']solver[\"']\s*,\s*[\"']mosek[\"']",
                    relative,
                )
            self._assert_mat_output_contract(relative, source, segment, output_pattern)


if __name__ == "__main__":
    unittest.main()
