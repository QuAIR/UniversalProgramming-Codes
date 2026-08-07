"""Source-level checks for the supported SDP implementation."""

import csv
from pathlib import Path
import re
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from verify_repository import (
    REQUIRED_SUMMARY_COLUMNS,
    VALID_STATUSES,
    validate_repository,
)


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
            rf"(?m)^[ \t]*repoRoot[ \t]*=[ \t]*" rf"{re.escape(root_call)};[ \t]*$"
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
        self.assertEqual(
            setup_matches, ["true" if requires_yalmip else "false"], relative
        )
        self.assertNotIn("/usr/local/", source, relative)

    def _save_calls(self, source):
        return re.findall(r"(?m)^[ \t]*save[ \t]*\(([^\r\n]*)\)[ \t]*;?[ \t]*$", source)

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
            "experiments/quair06/general_d/cert_d2_k3.m": (
                "certificates",
                "cert_d2_k3.mat",
            ),
            "experiments/quair06/general_d/cert_d2_k4.m": (
                "certificates",
                "cert_d2_k4.mat",
            ),
            "experiments/quair06/general_d/cert_d4_k2.m": (
                "certificates",
                "cert_d4_k2.mat",
            ),
            "experiments/quair06/general_d/cert_d5_k2.m": (
                "certificates",
                "cert_d5_k2.mat",
            ),
            "experiments/quair06/general_d/gamma_struct3.m": (
                "validated",
                "struct3_d%d_k%d.mat",
            ),
            "experiments/quair06/general_d/gamma_y3.m": ("validated", "y3_d%d_k%d.mat"),
            "experiments/quair06/general_d/diagnostics/gamma_struct.m": (
                "diagnostics",
                "struct_d%d_k%d.mat",
            ),
            "experiments/quair06/general_d/diagnostics/gamma_struct2.m": (
                "diagnostics",
                "struct2_d%d_k%d.mat",
            ),
            "experiments/quair06/general_d/diagnostics/gamma_y.m": (
                "diagnostics",
                "yalmip_d%d_k%d.mat",
            ),
        }
        for relative, (requires_yalmip, levels) in self.GENERAL_D_ENTRY_POINTS.items():
            source = self._read_general_d(relative)
            self._assert_entry_point_setup(relative, source, requires_yalmip, levels)
            if relative in outputs:
                segment, output_pattern = outputs[relative]
                self._assert_mat_output_contract(
                    relative, source, segment, output_pattern
                )
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
            "cost",
            "d",
            "k",
            "s",
            "b1",
            "b2",
            "p1",
            "p2",
            "cvx_status",
            "e1",
            "e2",
            "herm1",
            "herm2",
            "tpr1",
            "tpr2",
            "fres",
        )
        for name, (dimension, copies, fresh_channels) in certificates.items():
            relative = f"experiments/quair06/general_d/{name}"
            source = self._read_general_d(relative)
            self.assertEqual(
                re.findall(r"\bd\s*=\s*(\d+)\s*;", source), [str(dimension)], relative
            )
            self.assertEqual(
                re.findall(r"\bk\s*=\s*(\d+)\s*;", source), [str(copies)], relative
            )
            self.assertEqual(
                re.findall(r"\bs\s*=\s*(\d+)\s*;", source), ["500"], relative
            )
            self.assertEqual(
                len(re.findall(r"\brng\s*\(\s*0\s*\)\s*;", source)), 1, relative
            )
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
            "experiments/quair06/general_d/gamma_struct3.m": (
                "validated",
                "struct3_d%d_k%d.mat",
                "cvx",
                50,
            ),
            "experiments/quair06/general_d/gamma_y3.m": (
                "validated",
                "y3_d%d_k%d.mat",
                "yalmip",
                12,
            ),
            "experiments/quair06/general_d/diagnostics/gamma_struct.m": (
                "diagnostics",
                "struct_d%d_k%d.mat",
                "cvx",
                50,
            ),
            "experiments/quair06/general_d/diagnostics/gamma_struct2.m": (
                "diagnostics",
                "struct2_d%d_k%d.mat",
                "cvx",
                50,
            ),
            "experiments/quair06/general_d/diagnostics/gamma_y.m": (
                "diagnostics",
                "yalmip_d%d_k%d.mat",
                "yalmip",
                50,
            ),
        }
        for relative, (
            segment,
            output_pattern,
            solver,
            fresh_channels,
        ) in gamma_scripts.items():
            source = self._read_general_d(relative)
            self.assertEqual(
                re.findall(r"\bd\s*=\s*(\d+)\s*;", source), ["2"], relative
            )
            self.assertEqual(
                re.findall(r"\bk\s*=\s*(\d+)\s*;", source), ["5"], relative
            )
            self.assertEqual(
                re.findall(r"\bs\s*=\s*(\d+)\s*;", source), ["500"], relative
            )
            self.assertEqual(
                len(re.findall(r"\brng\s*\(\s*0\s*\)\s*;", source)), 1, relative
            )
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


class PublicDocumentationIntegrationTest(unittest.TestCase):
    EXPECTED_EXPERIMENT_IDS = {
        "UP-ANALYTIC-K1",
        "UP-D2-EXACT-K14",
        "UP-D2-K5-CANDIDATE",
        "UP-D2-K6-CHECKPOINT",
        "UP-GD-CVX-CANONICAL",
        "UP-GD-YALMIP-LARGE",
        "UP-GD-D3K4-POSTSOLVE",
        "UP-DIAGNOSTIC-CROSSCHECKS",
        "UP-D2-LINEAR-RELAXATION",
        "UP-GD-DEFECTIVE-BASELINE",
        "UP-FIXED-PROTOCOL-CHECK",
        "UP-PBT-RECOVERED-CLAIM",
    }
    REQUIRED_MANIFEST_FIELDS = (
        "Status",
        "Dimensions and copy counts",
        "Entry script",
        "Dependencies and solver",
        "Sample count",
        "Output artifacts",
        "Certificate or residual checks",
        "Historical source",
        "Known limitations",
    )
    EXPECTED_SUMMARY_ROWS = {
        ("2", "1"): (
            "5.500000",
            "analytic_formula_exact_sdp_check",
            "cvx-sdpt3",
            "500",
            "validated",
            "results/certified/kcopy_d2/exact_d2_k1.mat",
        ),
        ("2", "2"): (
            "2.713330",
            "exact_reduced_sdp",
            "cvx-sdpt3",
            "500",
            "validated",
            "results/certified/kcopy_d2/exact_d2_k2.mat",
        ),
        ("2", "3"): (
            "1.888291",
            "full_space_certified_sdp",
            "cvx-mosek",
            "500",
            "validated",
            "results/certified/general_d/cert_d2_k3.mat",
        ),
        ("2", "4"): (
            "1.529423",
            "full_space_certified_sdp",
            "cvx-mosek",
            "500",
            "validated",
            "results/certified/general_d/cert_d2_k4.mat",
        ),
        ("2", "5"): (
            "1.350907",
            "nullspace_structured_sdp",
            "cvx-mosek",
            "500",
            "validated",
            "results/certified/general_d/struct2_d2_k5.mat",
        ),
        ("3", "1"): ("15.222222", "analytic_formula", "analytic", "0", "validated", ""),
        ("3", "2"): (
            "7.456450",
            "hilbert_reduced_sdp",
            "cvx-sdpt3",
            "800",
            "validated",
            "results/diagnostic/historical_results_gamma_d3_k2_s800_r1.mat",
        ),
        ("3", "3"): (
            "4.882170",
            "nullspace_structured_sdp",
            "cvx-mosek",
            "500",
            "validated",
            "results/certified/general_d/struct2_d3_k3.mat",
        ),
        ("3", "4"): (
            "3.619643",
            "reduced_sdp_cross_check",
            "yalmip-mosek",
            "500",
            "diagnostic",
            "legacy/failed-runs/logs/y_d3k4_postsolve_terminated.log",
        ),
        ("4", "1"): ("29.125000", "analytic_formula", "analytic", "0", "validated", ""),
        ("4", "2"): (
            "14.366215",
            "exact_reduced_sdp",
            "cvx-mosek",
            "500",
            "validated",
            "results/certified/general_d/cert_d4_k2.mat",
        ),
        ("4", "3"): (
            "9.453850",
            "reduced_space_structured_sdp",
            "cvx-mosek",
            "500",
            "validated",
            "results/certified/general_d/struct3_d4_k3.mat",
        ),
        ("4", "4"): (
            "7.003853",
            "reduced_space_structured_sdp",
            "yalmip-mosek",
            "128",
            "validated",
            "results/certified/general_d/y3_d4_k4.mat",
        ),
        ("5", "1"): ("47.080000", "analytic_formula", "analytic", "0", "validated", ""),
        ("5", "2"): (
            "23.324402",
            "exact_reduced_sdp",
            "cvx-mosek",
            "500",
            "validated",
            "results/certified/general_d/cert_d5_k2.mat",
        ),
        ("5", "3"): (
            "15.410364",
            "reduced_space_structured_sdp",
            "yalmip-mosek",
            "256",
            "validated",
            "results/certified/general_d/y3_d5_k3.mat",
        ),
    }
    MANIFEST_CONTRACTS = {
        "UP-ANALYTIC-K1": {
            "status": "validated",
            "dimensions": ("`k=1`", "`d=2,3,4,5`"),
            "solver": ("analytic evaluation",),
            "samples": ("`0`",),
            "entries": (),
            "outputs": (
                "../results/summary.csv",
                "../results/certified/kcopy_d2/exact_d2_k1.mat",
            ),
            "limitations": (
                "does not by itself establish a bound uniform in both `d` and `k`",
            ),
        },
        "UP-D2-EXACT-K14": {
            "status": "validated",
            "dimensions": ("`d=2`", "`k=1,2,3,4`"),
            "solver": ("CVX", "QETLAB", "default SDPT3"),
            "samples": ("`500` programming samples", "`50` fresh-channel checks"),
            "entries": (
                "../experiments/quair06/kcopy_d2/run_exact_k14.m",
                "../src/matlab/kcopy_d2/gamma_k_d2_exact.m",
            ),
            "outputs": tuple(
                f"../results/certified/kcopy_d2/exact_d2_k{k}.mat" for k in range(1, 5)
            ),
            "limitations": ("finite CPTP samples", "not an exact symbolic proof"),
        },
        "UP-D2-K5-CANDIDATE": {
            "status": "diagnostic",
            "dimensions": ("`d=2`", "`k=5`"),
            "solver": ("CVX", "QETLAB", "SDPT3"),
            "samples": ("`500` programming samples", "`50` fresh-channel checks"),
            "entries": ("../experiments/quair06/kcopy_d2/run_exact_k56.m",),
            "outputs": (
                "../results/diagnostic/quair06_exact_d2_k5_saved_blocks.mat",
                "../results/logs/quair06_exact_k56_checkpoint.log",
                "../results/logs/quair06_exact_k56_checkpoint.csv",
            ),
            "limitations": (
                "`diagnostic_numerical_candidate`",
                "does not replace the canonical structured value",
            ),
        },
        "UP-D2-K6-CHECKPOINT": {
            "status": "incomplete",
            "dimensions": ("`d=2`", "`k=6`"),
            "solver": ("CVX SDP solver", "no completed solve"),
            "samples": ("`500` programming samples", "`50` fresh-channel checks"),
            "entries": ("../experiments/quair06/kcopy_d2/run_exact_k56.m",),
            "outputs": (
                "../results/diagnostic/quair06_exact_k56_checkpoint.mat",
                "../results/logs/quair06_exact_k56_checkpoint.log",
                "../results/logs/quair06_exact_k56_checkpoint.csv",
            ),
            "limitations": ("No `k=6` objective, feasible point, or certificate",),
        },
        "UP-GD-CVX-CANONICAL": {
            "status": "validated",
            "dimensions": ("`(d,k)=(2,3),(2,4),(2,5),(3,3),(4,2),(4,3),(5,2)`",),
            "solver": ("MATLAB, CVX, QETLAB, MOSEK",),
            "samples": (
                "`500`",
                "`200` for `d=2,k=3,4`",
                "`50` for structured records",
                "`25` for `d=5,k=2`",
            ),
            "entries": (
                "../experiments/quair06/general_d/cert_d2_k3.m",
                "../experiments/quair06/general_d/cert_d2_k4.m",
                "../experiments/quair06/general_d/cert_d4_k2.m",
                "../experiments/quair06/general_d/cert_d5_k2.m",
                "../legacy/server-snapshots/quair06-2026-08-07/pqga/struct2_k5.m",
                "../legacy/server-snapshots/quair06-2026-08-07/pqga/struct2_d3k3.m",
                "../legacy/server-snapshots/quair06-2026-08-07/pqga/struct3_d4k3.m",
                "../experiments/quair06/general_d/gamma_struct3.m",
                "../experiments/quair06/general_d/diagnostics/gamma_struct2.m",
            ),
            "outputs": tuple(
                f"../results/certified/general_d/{name}"
                for name in (
                    "cert_d2_k3.mat",
                    "cert_d2_k4.mat",
                    "struct2_d2_k5.mat",
                    "struct2_d3_k3.mat",
                    "cert_d4_k2.mat",
                    "struct3_d4_k3.mat",
                    "cert_d5_k2.mat",
                )
            ),
            "limitations": (
                "No supported direct entry currently reproduces the structured",
                "not be described as symbolic all-CPTP proofs",
            ),
        },
        "UP-GD-YALMIP-LARGE": {
            "status": "validated",
            "dimensions": ("`(d,k)=(4,4)`", "`(5,3)`"),
            "solver": ("MATLAB, YALMIP, QETLAB, MOSEK",),
            "samples": ("`128` and 12 fresh checks", "`256` and 12 fresh checks"),
            "entries": (
                "../legacy/server-snapshots/quair06-2026-08-07/pqga/y3_d4k4.m",
                "../legacy/server-snapshots/quair06-2026-08-07/pqga/y3_d5k3.m",
                "../experiments/quair06/general_d/gamma_y3.m",
            ),
            "outputs": (
                "../results/certified/general_d/y3_d4_k4.mat",
                "../results/certified/general_d/y3_d5_k3.mat",
                "../results/diagnostic/quair06_y3_d4_k3.mat",
                "../results/diagnostic/quair06_y3_d5_k2.mat",
            ),
            "limitations": (
                "no supported direct entry currently reproduces either canonical row",
                "Cross-check MATs are diagnostic",
            ),
        },
        "UP-GD-D3K4-POSTSOLVE": {
            "status": "diagnostic",
            "dimensions": ("`d=3`", "`k=4`"),
            "solver": ("CVX or YALMIP", "MOSEK"),
            "samples": ("`500`",),
            "entries": (
                "../legacy/server-snapshots/quair06-2026-08-07/pqga/struct2_d3k4.m",
                "../legacy/server-snapshots/quair06-2026-08-07/pqga/y_d3k4.m",
                "../experiments/quair06/general_d/diagnostics/gamma_struct2.m",
                "../experiments/quair06/general_d/diagnostics/gamma_y.m",
            ),
            "outputs": (
                "../legacy/failed-runs/logs/y_d3k4_postsolve_terminated.log",
                "../legacy/failed-runs/logs/struct2_d3k4_postsolve_terminated.log",
            ),
            "limitations": ("No full-space or completed reduced-space certificate",),
        },
        "UP-DIAGNOSTIC-CROSSCHECKS": {
            "status": "diagnostic",
            "dimensions": ("`d=2,3`", "`k=1,2,3`"),
            "solver": ("MATLAB, CVX, QETLAB", "usually SDPT3"),
            "samples": ("`300`, `500`, or `800`",),
            "entries": ("../legacy/general-d-baseline", "../legacy/failed-runs"),
            "outputs": (
                "../results/logs/brute_d2_k2.log",
                "../results/diagnostic/historical_results_gamma_d3_k2_s800_r1.mat",
                "../results/diagnostic/historical_results_brute_d2_k3_s300_r0.mat",
                "../results/mat-artifacts.json",
            ),
            "limitations": ("do not define rows in `results/summary.csv`",),
        },
        "UP-D2-LINEAR-RELAXATION": {
            "status": "legacy",
            "dimensions": ("`d=2`", "`k=1,2,3,4`"),
            "solver": ("MATLAB, CVX, QETLAB", "historical CVX solver configuration"),
            "samples": ("`500`",),
            "entries": ("../legacy/linear-relaxation/run_quair06_linear_k14.m",),
            "outputs": (
                "../results/diagnostic/historical_kcopy_d2_quair06_linear_k14.mat",
                "../results/diagnostic/quair06_full_vs_linear_k1_k3.mat",
            ),
            "limitations": (
                "lower-bound relaxation",
                "not equivalent to the full k-copy SDP",
            ),
        },
        "UP-GD-DEFECTIVE-BASELINE": {
            "status": "legacy",
            "dimensions": ("known defective for `k>=3`",),
            "solver": ("MATLAB, CVX, QETLAB", "may select MOSEK"),
            "samples": ("default `500`",),
            "entries": (
                "../legacy/general-d-baseline/gamma_k.m",
                "../legacy/general-d-baseline/generators",
            ),
            "outputs": (
                "../results/diagnostic",
                "provenance/legacy-task-5-manifest.json",
            ),
            "limitations": (
                "`PermuteSystems` convention is defective for `k>=3`",
                "archived and unsupported",
            ),
        },
        "UP-FIXED-PROTOCOL-CHECK": {
            "status": "incomplete",
            "dimensions": ("`d=2`", "`k=1,2,3`"),
            "solver": ("MATLAB, CVX, QETLAB, SDPT3",),
            "samples": ("historical deterministic construction",),
            "entries": ("../legacy/failed-runs/fixed_protocol_cost_check.m",),
            "outputs": ("../legacy/failed-runs/README.md",),
            "limitations": (
                "No `k=3` value is claimed",
                "not a supported upper-bound pipeline",
            ),
        },
        "UP-PBT-RECOVERED-CLAIM": {
            "status": "legacy",
            "dimensions": ("finite-`k` PBT-bound scripts",),
            "solver": ("no SDP solve is part of this entry",),
            "samples": ("Not applicable", "recovered analytic expression"),
            "entries": (
                "../legacy/server-snapshots/quair06-2026-08-07/pqga/pbt_bound/pbt_bound.py",
                "../legacy/server-snapshots/quair06-2026-08-07/pqga/pbt_bound/make_fig3.py",
            ),
            "outputs": (
                "../legacy/server-snapshots/quair06-2026-08-07/pqga/pbt_bound/README.md",
            ),
            "limitations": (
                "was not independently re-proven",
                "does not establish the converse",
            ),
        },
    }

    @staticmethod
    def _summary_rows():
        with (ROOT / "results/summary.csv").open(
            newline="", encoding="utf-8"
        ) as handle:
            return list(csv.DictReader(handle))

    @staticmethod
    def _manifest_sections():
        text = (ROOT / "docs/experiment-manifest.md").read_text(encoding="utf-8")
        matches = list(re.finditer(r"(?m)^## (UP-[A-Z0-9-]+)\s*$", text))
        sections = {}
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            sections[match.group(1)] = text[match.end() : end]
        return sections

    @staticmethod
    def _manifest_field(section, field):
        match = re.search(rf"(?m)^- \*\*{re.escape(field)}:\*\* (.+)$", section)
        if match is None:
            raise AssertionError(f"missing manifest field: {field}")
        return match.group(1)

    @classmethod
    def _manifest_links(cls, section, field):
        return tuple(
            re.findall(r"\[[^]]+\]\(([^)]+)\)", cls._manifest_field(section, field))
        )

    def test_required_public_docs_and_supported_entry_points_exist(self):
        required = (
            "README.md",
            "docs/experiment-manifest.md",
            "docs/mathematical-reduction/MATH_REFERENCE.md",
            "docs/provenance/README.md",
            "docs/provenance/quair06-live-inventory.json",
            "experiments/quair06/README.md",
            "experiments/quair06/kcopy_d2/run_exact_k14.m",
            "experiments/quair06/kcopy_d2/run_exact_k56.m",
            "experiments/quair06/general_d/gamma_struct3.m",
            "experiments/quair06/general_d/gamma_y3.m",
            "results/mat-artifacts.json",
            "results/summary.csv",
        )
        for relative in required:
            self.assertTrue((ROOT / relative).is_file(), relative)

    def test_summary_schema_and_public_status_vocabulary(self):
        with (ROOT / "results/summary.csv").open(
            newline="", encoding="utf-8"
        ) as handle:
            reader = csv.DictReader(handle)
            self.assertEqual(reader.fieldnames, REQUIRED_SUMMARY_COLUMNS)
            rows = list(reader)
        self.assertEqual(len(rows), 16)
        self.assertTrue({row["status"] for row in rows} <= VALID_STATUSES)

        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        manifest = (ROOT / "docs/experiment-manifest.md").read_text(encoding="utf-8")
        for status in ("validated", "diagnostic", "legacy", "incomplete"):
            self.assertRegex(readme, rf"(?m)^\| \*\*{status}\*\* \| .+\|$")
            self.assertRegex(manifest, rf"(?m)^- `{status}`: .+[.;]$")

    def test_every_manifest_family_has_all_fields_and_existing_targets(self):
        sections = self._manifest_sections()
        self.assertEqual(set(sections), self.EXPECTED_EXPERIMENT_IDS)
        for experiment_id, section in sections.items():
            for field in self.REQUIRED_MANIFEST_FIELDS:
                self.assertRegex(
                    section,
                    rf"(?m)^- \*\*{re.escape(field)}:\*\* .+$",
                    f"{experiment_id}: missing {field}",
                )

            status = re.search(r"(?m)^- \*\*Status:\*\* `([^`]+)`", section)
            self.assertIsNotNone(status, experiment_id)
            self.assertIn(status.group(1), VALID_STATUSES, experiment_id)

            for field in ("Entry script", "Output artifacts"):
                line = re.search(
                    rf"(?m)^- \*\*{re.escape(field)}:\*\* (.+)$", section
                ).group(1)
                for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", line):
                    self.assertFalse(target.startswith(("http://", "https://")))
                    resolved = (ROOT / "docs" / target).resolve()
                    self.assertTrue(resolved.exists(), f"{experiment_id}: {target}")

    def test_manifest_families_encode_expected_scientific_facts(self):
        sections = self._manifest_sections()
        self.assertEqual(set(self.MANIFEST_CONTRACTS), self.EXPECTED_EXPERIMENT_IDS)
        for experiment_id, contract in self.MANIFEST_CONTRACTS.items():
            section = sections[experiment_id]
            status = self._manifest_field(section, "Status")
            self.assertEqual(status, f"`{contract['status']}`", experiment_id)

            for field, contract_key in (
                ("Dimensions and copy counts", "dimensions"),
                ("Dependencies and solver", "solver"),
                ("Sample count", "samples"),
                ("Known limitations", "limitations"),
            ):
                value = self._manifest_field(section, field)
                for marker in contract[contract_key]:
                    self.assertIn(marker, value, f"{experiment_id} {field}: {marker}")

            self.assertEqual(
                set(self._manifest_links(section, "Entry script")),
                set(contract["entries"]),
                f"{experiment_id}: entry scripts",
            )
            self.assertEqual(
                set(self._manifest_links(section, "Output artifacts")),
                set(contract["outputs"]),
                f"{experiment_id}: output artifacts",
            )

    def test_historical_general_d_wrappers_have_recorded_parameters(self):
        wrappers = {
            "struct2_k5.m": (2, 5, 500, 50, "cvx", "struct2_d%d_k%d.mat"),
            "struct2_d3k3.m": (3, 3, 500, 50, "cvx", "struct2_d%d_k%d.mat"),
            "struct3_d4k3.m": (4, 3, 500, 50, "cvx", "struct3_d%d_k%d.mat"),
            "y3_d4k4.m": (4, 4, 128, 12, "yalmip", "y3_d%d_k%d.mat"),
            "y3_d5k3.m": (5, 3, 256, 12, "yalmip", "y3_d%d_k%d.mat"),
            "struct2_d3k4.m": (3, 4, 500, 50, "cvx", "struct2_d%d_k%d.mat"),
            "y_d3k4.m": (3, 4, 500, 50, "yalmip", "yalmip_d%d_k%d.mat"),
        }
        base = ROOT / "legacy/server-snapshots/quair06-2026-08-07/pqga"
        for name, (
            dimension,
            copies,
            samples,
            fresh,
            backend,
            output,
        ) in wrappers.items():
            source = (base / name).read_text(encoding="utf-8")
            self.assertRegex(
                source,
                rf"(?m)^d\s*=\s*{dimension};\s*k\s*=\s*{copies};\s*s\s*=\s*{samples};",
            )
            self.assertRegex(source, rf"\bnf\s*=\s*{fresh}\s*;")
            if backend == "cvx":
                self.assertRegex(source, r"\bcvx_solver\s+mosek\b", name)
            else:
                self.assertRegex(
                    source,
                    r"sdpsettings\s*\([^\r\n]*['\"]solver['\"]\s*,\s*['\"]mosek['\"]",
                    name,
                )
            self.assertIn(f'sprintf("results/{output}",d,k)', source, name)

    def test_exact_d2_entry_points_use_documented_defaults(self):
        config = (ROOT / "src/matlab/up_config.m").read_text(encoding="ascii")
        solver = (ROOT / "src/matlab/kcopy_d2/gamma_k_d2_exact.m").read_text(
            encoding="ascii"
        )
        self.assertIn("'UP_SDP_SOLVER', 'sdpt3'", config)
        self.assertIn("defaults.solver = 'sdpt3';", solver)
        self.assertIn("defaults.s = 500;", solver)
        self.assertIn("defaults.certFresh = 50;", solver)

        runners = {
            "run_exact_k14.m": "ks = (1:4).';",
            "run_exact_k56.m": "ks = [5; 6];",
        }
        for name, copies in runners.items():
            source = (ROOT / "experiments/quair06/kcopy_d2" / name).read_text(
                encoding="ascii"
            )
            self.assertIn("opts.solver = cfg.solver;", source, name)
            self.assertIn("opts.s = 500;", source, name)
            self.assertIn("opts.certFresh = 50;", source, name)
            self.assertIn(copies, source, name)

    def test_all_summary_rows_match_the_canonical_contract(self):
        rows = {(row["d"], row["k"]): row for row in self._summary_rows()}
        self.assertEqual(set(rows), set(self.EXPECTED_SUMMARY_ROWS))
        fields = ("gamma", "method", "solver", "sample_count", "status", "artifact")
        for key, values in self.EXPECTED_SUMMARY_ROWS.items():
            row = rows[key]
            actual = tuple(row[field] for field in fields)
            self.assertEqual(actual, values, key)
            artifact = row["artifact"]
            if artifact:
                self.assertTrue((ROOT / artifact).is_file(), artifact)

    def test_output_preservation_requires_a_new_results_root(self):
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        run_guide = (ROOT / "experiments/quair06/README.md").read_text(encoding="utf-8")
        for text in (root_readme, run_guide):
            self.assertIn("new `UP_RESULTS_ROOT`", text)
            self.assertRegex(text, r"truncat(?:e|es)")
            self.assertRegex(text, r"replace(?:s)? (?:its |the )?PID\s+file")
            self.assertRegex(text, r"rewrite")
            self.assertRegex(text, r"recursively\s+delete")

    def test_readme_canonical_table_exactly_matches_summary(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        table = readme.split("<!-- canonical-summary:start -->", 1)[1].split(
            "<!-- canonical-summary:end -->", 1
        )[0]
        parsed = []
        for line in table.splitlines():
            match = re.fullmatch(
                r"\| (\d+) \| (\d+) \| ([0-9]+\.[0-9]{6}) \| "
                r"(validated|diagnostic|legacy|incomplete) \|",
                line,
            )
            if match:
                parsed.append(match.groups())
        expected = [
            (row["d"], row["k"], row["gamma"], row["status"])
            for row in self._summary_rows()
        ]
        self.assertEqual(parsed, expected)

    def test_live_reconciliation_is_linked_and_factual(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        run_guide = (ROOT / "experiments/quair06/README.md").read_text(encoding="utf-8")
        for text in (readme, run_guide):
            self.assertIn("205 files", text)
            self.assertRegex(text, r"zero\s+source\s+SHA-256\s+mismatches")
            self.assertIn("No remote job was started, stopped, or modified", text)
            self.assertIn("quair06-live-inventory.json", text)

    def test_complete_repository_passes_static_verifier(self):
        self.assertEqual(validate_repository(ROOT), [])


if __name__ == "__main__":
    unittest.main()
