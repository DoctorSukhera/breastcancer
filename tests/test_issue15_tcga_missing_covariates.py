import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'analysis' / '01_tcga_age_association.py'


class TestIssue15TCGAMissingCovariates(unittest.TestCase):
    def test_missing_clinical_covariates_are_retained_as_unknown(self):
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            n = 30
            ids = [f'S{i:02d}' for i in range(n)]
            age = np.linspace(35, 80, n)

            expr = pd.DataFrame({'gene': ['GENE1']})
            for i, sid in enumerate(ids):
                expr[sid] = [0.08 * age[i] + 0.02 * np.sin(i)]
            expr_path = td / 'expr.csv'
            expr.to_csv(expr_path, index=False)

            clinical = pd.DataFrame({
                'sample_id': ids,
                'age': age,
                'ER': ['Positive' if i % 2 else 'Negative' for i in range(n)],
                'PR': ['Positive' if i % 3 else 'Negative' for i in range(n)],
                'HER2': ['Negative' if i % 4 else 'Positive' for i in range(n)],
                'stage': ['I', 'II', 'III'] * 10,
            })
            clinical.loc[1, 'ER'] = np.nan
            clinical.loc[2, 'ER'] = 'Not Available'
            clinical.loc[3, 'PR'] = ''
            clinical.loc[4, 'HER2'] = 'null'
            clinical.loc[5, 'stage'] = np.nan
            clinical.loc[6, 'stage'] = '[Not Reported]'
            clin_path = td / 'clinical.csv'
            clinical.to_csv(clin_path, index=False)

            genage_path = td / 'genage.csv'
            pd.DataFrame({'gene': ['GENE1']}).to_csv(genage_path, index=False)
            outdir = td / 'out'

            subprocess.run([
                sys.executable, str(SCRIPT),
                '--expression', str(expr_path),
                '--clinical', str(clin_path),
                '--genage', str(genage_path),
                '--outdir', str(outdir),
            ], check=True, cwd=ROOT, capture_output=True, text=True)

            adj = pd.read_csv(outdir / 'tcga_adjusted_age_association.csv')
            self.assertEqual(len(adj), 1)
            self.assertEqual(int(adj.loc[0, 'n']), n)

            miss = pd.read_csv(outdir / 'tcga_covariate_missingness_summary.csv').set_index('covariate')
            self.assertEqual(int(miss.loc['ER', 'n_explicit_missing_category']), 2)
            self.assertEqual(int(miss.loc['PR', 'n_explicit_missing_category']), 1)
            self.assertEqual(int(miss.loc['HER2', 'n_explicit_missing_category']), 1)
            self.assertEqual(int(miss.loc['stage', 'n_explicit_missing_category']), 2)
            self.assertEqual(set(miss['explicit_missing_category']), {'Unknown'})

    def test_adjusted_model_does_not_complete_case_delete_categorical_covariates(self):
        src = SCRIPT.read_text()
        self.assertNotIn("dropna(subset=['expr','age_z',args.er_col", src)
        self.assertIn("d=d.dropna(subset=['expr','age_z'])", src)
        self.assertIn('retain_missing_as_category', src)


if __name__ == '__main__':
    unittest.main(verbosity=2)
