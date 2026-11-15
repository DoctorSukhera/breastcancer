import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / 'analysis' / 'run_molecular_pipeline.py'


def make_inputs(base: Path):
    n=30
    ids=[f'S{i:02d}' for i in range(n)]
    age=np.arange(40,70,dtype=float)
    genes=['G1','G2','G3','G4','G5']
    expr=pd.DataFrame({'gene':genes})
    for j,s in enumerate(ids):
        expr[s]=[age[j]*0.10+k*0.01 for k in range(len(genes))]
    expr.to_csv(base/'tcga_expr.csv',index=False)
    clin=pd.DataFrame({
        'sample_id':ids,'age':age,
        'ER':[j%2 for j in range(n)],
        'PR':[(j//2)%2 for j in range(n)],
        'HER2':[(j//3)%2 for j in range(n)],
        'stage':['I' if j<15 else 'II' for j in range(n)],
    })
    clin.to_csv(base/'tcga_clin.csv',index=False)
    pd.DataFrame({'gene':genes}).to_csv(base/'genage.csv',index=False)

    geo_ids=[f'GEO{i:02d}' for i in range(12)]
    geo_age=np.arange(45,57,dtype=float)
    gx=pd.DataFrame({'probe_id':[f'P{i}' for i in range(5)]})
    for j,s in enumerate(geo_ids): gx[s]=[geo_age[j]*0.1+k*0.02 for k in range(5)]
    gx.to_csv(base/'geo_expr.csv',index=False)
    pd.DataFrame({'probe_id':[f'P{i}' for i in range(5)],'gene_symbol':genes}).to_csv(base/'geo_ann.csv',index=False)
    pd.DataFrame({'sample_id':geo_ids,'age':geo_age}).to_csv(base/'geo_meta.csv',index=False)

    edges=[]
    for i in range(4):
        edges.append({'protein1':f'9606.P{i}','protein2':f'9606.P{i+1}','combined_score':900})
    pd.DataFrame(edges).to_csv(base/'string_edges.tsv',sep='\t',index=False)
    pd.DataFrame({'protein':[f'9606.P{i}' for i in range(5)],'gene':genes}).to_csv(base/'string_map.tsv',sep='\t',index=False)
    (base/'go.gmt').write_text('GO_T1\tdesc\tG1\tG2\tG3\nGO_T2\tdesc\tG1\tG2\nGO_T3\tdesc\tG4\tG5\n',encoding='utf-8')
    (base/'kegg.gmt').write_text('KEGG_T1\tdesc\tG1\tG2\tG3\nKEGG_T2\tdesc\tG3\tG4\tG5\n',encoding='utf-8')


def make_config(base: Path, out: Path):
    cfg={
        'output_dir':str(out),
        'inputs':{
            'tcga_expression':str(base/'tcga_expr.csv'),
            'tcga_clinical':str(base/'tcga_clin.csv'),
            'genage':str(base/'genage.csv'),
            'geo_series_matrix':str(base/'geo_expr.csv'),
            'geo_annotation':str(base/'geo_ann.csv'),
            'geo_metadata':str(base/'geo_meta.csv'),
            'string_edges':str(base/'string_edges.tsv'),
            'string_mapping':str(base/'string_map.tsv'),
            'go_gene_sets':str(base/'go.gmt'),
            'kegg_gene_sets':str(base/'kegg.gmt'),
        },
        'settings':{'permutations':3,'bootstrap_resamples':5,'permutation_seed':7,'bootstrap_seed':7}
    }
    p=base/'config.json';p.write_text(json.dumps(cfg),encoding='utf-8');return p


with tempfile.TemporaryDirectory() as td:
    base=Path(td);make_inputs(base);out=base/'out';cfg=make_config(base,out)
    chk=subprocess.run([sys.executable,str(RUNNER),'--config',str(cfg),'--check-only'],cwd=ROOT,capture_output=True,text=True)
    assert chk.returncode==0, chk.stderr
    assert 'MOLECULAR INPUT VALIDATION: PASS' in chk.stdout
    assert not out.exists(), 'check-only must not create partial output'

    run=subprocess.run([sys.executable,str(RUNNER),'--config',str(cfg)],cwd=ROOT,capture_output=True,text=True)
    assert run.returncode==0, run.stderr + '\n' + run.stdout
    expected=[
        out/'01_tcga/tcga_adjusted_age_association.csv',
        out/'adjusted_significant_genes.csv',
        out/'02_external_replication.csv',
        out/'03_er_stratified.csv',
        out/'04_string/string_thresholds.csv',
        out/'05_enrichment/enrichment_computed.csv',
        out/'05_enrichment/enrichment_analysis_audit.json',
        out/'05_enrichment/representative_modules.csv',
        out/'06_permutation_counts.csv',
        out/'06_permutation_summary.json',
        out/'07_candidate_bootstrap.csv',
        out/'08_complete_tables/M1_tcga_all_curated_gene_statistics.csv',
        out/'08_complete_tables/MOLECULAR_RESULT_TABLES_MANIFEST.json',
        out/'MOLECULAR_RUN_MANIFEST.json',
    ]
    assert all(p.exists() for p in expected), [str(p) for p in expected if not p.exists()]
    manifest=json.loads((out/'MOLECULAR_RUN_MANIFEST.json').read_text())
    assert manifest['status']=='complete'
    assert Path(manifest['derived_outputs']['adjusted_significant_genes']).exists()
    assert Path(manifest['derived_outputs']['complete_molecular_tables_manifest']).exists()

with tempfile.TemporaryDirectory() as td:
    base=Path(td);make_inputs(base);out=base/'out';cfg=make_config(base,out)
    (base/'string_edges.tsv').unlink()
    bad=subprocess.run([sys.executable,str(RUNNER),'--config',str(cfg)],cwd=ROOT,capture_output=True,text=True)
    assert bad.returncode!=0
    assert not out.exists(), 'input validation must fail before creating output directory'

status=subprocess.run([sys.executable,str(RUNNER),'--release-status'],cwd=ROOT,capture_output=True,text=True)
assert status.returncode==0
assert 'EXTERNAL INPUTS REQUIRED' in status.stdout

src=(ROOT/'run_all.py').read_text()
assert '--molecular-config' in src
assert "--release-status" in src
assert "--require-outside-repo" in src

print('Issue 17 molecular orchestration tests: PASS')
