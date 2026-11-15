import hashlib
import tempfile
import unittest
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class TestIssue14DeterministicRepositoryHashes(unittest.TestCase):
    def test_figure_generators_lock_pdf_svg_metadata_and_ids(self):
        s1=(ROOT/'scripts'/'generate_figure1.py').read_text()
        s2=(ROOT/'scripts'/'generate_figures_2_6.py').read_text()
        for src in (s1,s2):
            self.assertIn('svg.hashsalt', src)
            self.assertIn('CreationDate', src)
            self.assertIn('ModDate', src)
            self.assertIn('Date', src)

    def test_representative_pdf_svg_are_byte_stable(self):
        old=plt.rcParams.get('svg.hashsalt')
        plt.rcParams['svg.hashsalt']='ageaware-bc-figures-v1'
        try:
            with tempfile.TemporaryDirectory() as td:
                td=Path(td)
                def render(tag):
                    fig,ax=plt.subplots(figsize=(2,1.5))
                    ax.plot([0,1],[0,1]); ax.set_title('determinism')
                    pdf=td/f'{tag}.pdf'; svg=td/f'{tag}.svg'
                    fig.savefig(pdf,metadata={'CreationDate':None,'ModDate':None,'Creator':'AgeAware BC reproducible figure pipeline','Producer':'Matplotlib 3.10.8'})
                    fig.savefig(svg,metadata={'Date':None,'Creator':'AgeAware BC reproducible figure pipeline'})
                    plt.close(fig)
                    return digest(pdf),digest(svg)
                self.assertEqual(render('a'),render('b'))
        finally:
            plt.rcParams['svg.hashsalt']=old

    def test_manifest_utility_excludes_self_and_transient_python_cache(self):
        src=(ROOT/'scripts'/'repository_manifest.py').read_text()
        self.assertIn('SHA256_MANIFEST.csv',src)
        self.assertIn('__pycache__',src)
        self.assertIn('.pyc',src)

if __name__=='__main__':
    unittest.main(verbosity=2)
