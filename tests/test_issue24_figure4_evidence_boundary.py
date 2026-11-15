from pathlib import Path
import csv
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generate_figures_2_6.py"
SOURCE = ROOT / "data" / "source_tables"
LEGACY = ROOT / "data" / "legacy_unverified" / "figure4"


class Figure4EvidenceBoundaryTests(unittest.TestCase):
    def test_unsupported_module_tables_are_not_active_sources(self):
        self.assertFalse((SOURCE / "Figure4_representative_modules.csv").exists())
        self.assertFalse((SOURCE / "Figure4_candidate_module_matrix.csv").exists())
        self.assertTrue((LEGACY / "Figure4_representative_modules_UNVERIFIED.csv").exists())
        self.assertTrue((LEGACY / "Figure4_candidate_module_matrix_UNVERIFIED.csv").exists())
        note = (LEGACY / "README.md").read_text()
        self.assertIn("not active evidence", note.lower())
        self.assertIn("no publication figure reads them", note.lower())

    def test_plotting_code_has_no_module_level_empirical_fallback(self):
        text = SCRIPT.read_text()
        forbidden = [
            "FIG4_MODULES", "FIG4_MATRIX", "Figure4_representative_modules.csv",
            "Figure4_candidate_module_matrix.csv", "Pathways in cancer",
            "candidate×module matrix", "-np.log10(top10[\"adjusted_p\"])",
        ]
        for token in forbidden:
            self.assertNotIn(token, text)
        self.assertIn('Figure4_enrichment_counts.csv', text)
        self.assertIn('Exact module identities', text)

    def test_active_aggregate_counts_are_internally_consistent(self):
        with (SOURCE / "Figure4_enrichment_counts.csv").open(newline="") as f:
            row = next(csv.DictReader(f))
        ints = {k: int(float(row[k])) for k in [
            "total_tested", "go_tested", "kegg_tested", "total_significant",
            "go_significant", "kegg_significant", "clustered_terms",
            "representative_modules",
        ]}
        self.assertEqual(ints["go_tested"] + ints["kegg_tested"], ints["total_tested"])
        self.assertEqual(ints["go_significant"] + ints["kegg_significant"], ints["total_significant"])
        self.assertLessEqual(ints["representative_modules"], ints["clustered_terms"])
        self.assertLessEqual(ints["clustered_terms"], ints["total_significant"])
        self.assertLessEqual(ints["total_significant"], ints["total_tested"])
        j = float(row["jaccard_threshold"])
        self.assertGreater(j, 0)
        self.assertLessEqual(j, 1)


if __name__ == "__main__":
    unittest.main()
