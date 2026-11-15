import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'analysis' / '06_permutation_bootstrap.py'


class TestIssue16PermutationStratification(unittest.TestCase):
    def _write_fixture(self, td: Path):
        td.mkdir(parents=True, exist_ok=True)
        rng = np.random.default_rng(7)
        n = 48
        ids = [f'S{i:02d}' for i in range(n)]
        age = np.linspace(35, 82, n)
        er = np.array(['Positive'] * 20 + ['Negative'] * 20 + ['Unknown'] * 8, dtype=object)
        er[42] = np.nan
        er[43] = 'Not Available'
        pr = np.array(['Positive' if i % 2 else 'Negative' for i in range(n)], dtype=object)

        expr = pd.DataFrame({'gene': ['GENE1', 'GENE2', 'GENE3']})
        for i, sid in enumerate(ids):
            expr[sid] = [
                0.09 * age[i] + rng.normal(0, 0.12),
                -0.07 * age[i] + rng.normal(0, 0.15),
                rng.normal(0, 1.0),
            ]
        expr_path = td / 'expr.csv'; expr.to_csv(expr_path, index=False)
        clinical = pd.DataFrame({'sample_id': ids, 'age': age, 'ER': er, 'PR': pr})
        clin_path = td / 'clinical.csv'; clinical.to_csv(clin_path, index=False)
        genes_path = td / 'genes.csv'; pd.DataFrame({'gene': ['GENE1','GENE2','GENE3']}).to_csv(genes_path, index=False)
        return expr_path, clin_path, genes_path

    def _run(self, td: Path, extra=None, stem='default'):
        expr, clin, genes = self._write_fixture(td)
        out = td / f'{stem}.csv'
        cmd = [
            sys.executable, str(SCRIPT), '--expression', str(expr), '--clinical', str(clin),
            '--genes', str(genes), '--permutations', '25', '--seed', '123', '--out', str(out)
        ]
        if extra:
            cmd.extend(extra)
        subprocess.run(cmd, check=True, cwd=ROOT, capture_output=True, text=True)
        summary = json.loads((td / f'{stem}_summary.json').read_text())
        return pd.read_csv(out), summary

    def test_default_matches_manuscript_er_only_design(self):
        with tempfile.TemporaryDirectory() as tmp:
            td = Path(tmp)
            counts_default, s_default = self._run(td / 'a', stem='perm')
            counts_explicit, s_explicit = self._run(td / 'b', extra=['--strata','ER'], stem='perm')
            pd.testing.assert_frame_equal(counts_default, counts_explicit)
            self.assertEqual(s_default['strata_columns'], ['ER'])
            self.assertTrue(s_default['primary_manuscript_design'])
            self.assertEqual(s_default['stratum_sizes'], s_explicit['stratum_sizes'])

    def test_missing_er_is_explicit_unknown_stratum(self):
        with tempfile.TemporaryDirectory() as tmp:
            td = Path(tmp) / 'x'
            _, summary = self._run(td, stem='perm')
            self.assertIn('Unknown', summary['stratum_sizes'])
            # Six original Unknown plus two missing/placeholder values => 8 total.
            self.assertEqual(summary['stratum_sizes']['Unknown'], 8)
            self.assertEqual(sum(summary['stratum_sizes'].values()), summary['n_matched_samples'])

    def test_joint_stratification_requires_explicit_override(self):
        with tempfile.TemporaryDirectory() as tmp:
            td = Path(tmp) / 'x'
            _, summary = self._run(td, extra=['--strata','ER,PR'], stem='perm')
            self.assertEqual(summary['strata_columns'], ['ER','PR'])
            self.assertFalse(summary['primary_manuscript_design'])
            self.assertGreater(summary['n_strata'], 3)

    def test_source_default_is_not_joint_er_pr_her2_stage(self):
        src = SCRIPT.read_text()
        self.assertIn("--strata', default='ER'", src)
        self.assertNotIn("default='ER,PR,HER2,stage'", src)
        self.assertIn('retain_missing_as_category', src)


if __name__ == '__main__':
    unittest.main(verbosity=2)
