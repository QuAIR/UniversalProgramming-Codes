"""Source-level checks for the supported SDP implementation."""

import csv
from pathlib import Path
import re
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from verify_repository import REQUIRED_SUMMARY_COLUMNS, VALID_STATUSES, validate_repository


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
            sections[match.group(1)] = text[match.end():end]
        return sections

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
        manifest = (ROOT / "docs/experiment-manifest.md").read_text(
            encoding="utf-8"
        )
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
        run_guide = (ROOT / "experiments/quair06/README.md").read_text(
            encoding="utf-8"
        )
        for text in (readme, run_guide):
            self.assertIn("205 files", text)
            self.assertRegex(text, r"zero\s+source\s+SHA-256\s+mismatches")
            self.assertIn("No remote job was started, stopped, or modified", text)
            self.assertIn("quair06-live-inventory.json", text)

    def test_complete_repository_passes_static_verifier(self):
        self.assertEqual(validate_repository(ROOT), [])


if __name__ == "__main__":
    unittest.main()
