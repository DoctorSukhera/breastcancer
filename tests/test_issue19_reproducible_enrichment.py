import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
ORA=ROOT/'analysis'/'05_enrichment_analysis.py'
REDUCE=ROOT/'analysis'/'05_enrichment_redundancy.py'

with tempfile.TemporaryDirectory() as td:
    b=Path(td)
    pd.DataFrame({'gene':['A','B','C','D']}).to_csv(b/'genes.csv',index=False)
    (b/'go.gmt').write_text(
        'GO_AB\tdesc\tA\tB\n'
        'GO_ABC\tdesc\tA\tB\tC\n'
        'GO_XYZ\tdesc\tX\tY\tZ\n',encoding='utf-8')
    (b/'kegg.gmt').write_text(
        'KEGG_CD\tdesc\tC\tD\n'
        'KEGG_AX\tdesc\tA\tX\n',encoding='utf-8')
    out=b/'out'
    cmd=[sys.executable,str(ORA),'--genes',str(b/'genes.csv'),
         '--go-gene-sets',str(b/'go.gmt'),'--kegg-gene-sets',str(b/'kegg.gmt'),
         '--go-library-name','GO_TEST','--kegg-library-name','KEGG_TEST','--outdir',str(out)]
    r1=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
    assert r1.returncode==0, r1.stderr+'\n'+r1.stdout
    d1=pd.read_csv(out/'enrichment_computed.csv')
    assert len(d1)==5
    assert set(d1.source)=={'GO_TEST','KEGG_TEST'}
    assert {'p_value','adjusted_p','overlap_n','query_n','term_size','background_n','genes'}.issubset(d1.columns)
    assert d1.adjusted_p.between(0,1).all()
    audit=json.loads((out/'enrichment_analysis_audit.json').read_text())
    assert audit['go_gene_set_sha256'] and len(audit['go_gene_set_sha256'])==64
    assert audit['kegg_gene_set_sha256'] and len(audit['kegg_gene_set_sha256'])==64
    assert audit['multiple_testing']=='Benjamini-Hochberg within each source library'

    # Deterministic local snapshots must reproduce byte-identical numerical CSV.
    before=(out/'enrichment_computed.csv').read_bytes()
    r2=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True);assert r2.returncode==0
    assert before==(out/'enrichment_computed.csv').read_bytes()

    rr=subprocess.run([sys.executable,str(REDUCE),'--enrichment',str(out/'enrichment_computed.csv'),
                       '--top','5','--jaccard','0.40','--outdir',str(out)],cwd=ROOT,capture_output=True,text=True)
    assert rr.returncode==0, rr.stderr+'\n'+rr.stdout
    assert (out/'enrichment_all_terms.csv').exists()
    assert (out/'representative_modules.csv').exists()

runner=(ROOT/'analysis'/'run_molecular_pipeline.py').read_text()
assert 'analysis/05_enrichment_analysis.py' in runner
assert 'enrichment_computed.csv' in runner
assert 'go_gene_sets' in runner and 'kegg_gene_sets' in runner
assert 'enrichment_table' not in runner
print('Issue 19 reproducible enrichment tests: PASS')
