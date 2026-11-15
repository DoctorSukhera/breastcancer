#!/usr/bin/env python3
from pathlib import Path
import json, subprocess, tempfile
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / 'adapters' / 'tcga_blca_adapter.py'


def run(args, expect=0):
    p = subprocess.run(['python', str(ADAPTER), *args], text=True, capture_output=True)
    assert p.returncode == expect, (p.returncode, p.stdout, p.stderr)
    return p

with tempfile.TemporaryDirectory() as td:
    td = Path(td)

    # 1) gene x sample; clinical header normalization; missing token parsing.
    expr = pd.DataFrame({
        'Gene Symbol':['tp53','esr1','egfr'],
        'S1':[1.0,2.0,3.0], 'S2':[2.0,'NA',4.0], 'S3':[3.0,4.0,5.0],
    })
    clin = pd.DataFrame({'Sample ID':['S1','S2','S3'], 'Age at Diagnosis':[55,'Not Reported',70]})
    expr.to_csv(td/'expr1.csv',index=False); clin.to_csv(td/'clin1.csv',index=False)
    out1=td/'out1'
    run(['--expression',str(td/'expr1.csv'),'--clinical',str(td/'clin1.csv'),'--outdir',str(out1)])
    a=json.loads((out1/'adapter_audit.json').read_text())
    assert a['status']=='PASS' and a['expression_orientation']=='gene_by_sample'
    assert a['clinical_sample_column']=='sample_id' and a['gene_namespace_output']=='symbol'
    assert a['n_aligned_samples']==3 and a['n_missing_tokens_expression']>=1 and a['n_missing_tokens_clinical']>=1
    e=pd.read_csv(out1/'expression_common_schema.csv',index_col=0)
    assert set(e.index)=={'TP53','ESR1','EGFR'} and e.columns.tolist()==['S1','S2','S3']

    # 2) sample x gene orientation + Ensembl version stripping + explicit mapping to symbols.
    expr2=pd.DataFrame({
        'Participant Barcode':['P1','P2','P3'],
        'ENSG000001.5':[1,2,3], 'ENSG000002.1':[4,5,6],
    })
    clin2=pd.DataFrame({'participant id':['P1','P2','P3'],'age':[60,61,62]})
    mapping=pd.DataFrame({'ensembl id':['ENSG000001','ENSG000002'],'gene symbol':['GENEA','GENEB']})
    expr2.to_csv(td/'expr2.csv',index=False); clin2.to_csv(td/'clin2.csv',index=False); mapping.to_csv(td/'map.csv',index=False)
    out2=td/'out2'
    run(['--expression',str(td/'expr2.csv'),'--clinical',str(td/'clin2.csv'),
         '--expression-sample-col','Participant Barcode','--gene-namespace','ensembl',
         '--gene-mapping',str(td/'map.csv'),'--outdir',str(out2)])
    a2=json.loads((out2/'adapter_audit.json').read_text())
    assert a2['expression_orientation']=='sample_by_gene' and a2['gene_namespace_output']=='symbol'
    e2=pd.read_csv(out2/'expression_common_schema.csv',index_col=0)
    assert e2.index.tolist()==['GENEA','GENEB'] and e2.columns.tolist()==['P1','P2','P3']

    # 3) TCGA participant linkage is explicit/deterministic and does not guess sample selection.
    expr3=pd.DataFrame({'gene':['TP53','ESR1'], 'TCGA-AB-1234-01A':[1,2], 'TCGA-CD-5678-01A':[3,4]})
    clin3=pd.DataFrame({'case_submitter_id':['TCGA-AB-1234','TCGA-CD-5678'],'age':[50,70]})
    expr3.to_csv(td/'expr3.csv',index=False); clin3.to_csv(td/'clin3.csv',index=False)
    out3=td/'out3'
    run(['--expression',str(td/'expr3.csv'),'--clinical',str(td/'clin3.csv'),'--outdir',str(out3)])
    a3=json.loads((out3/'adapter_audit.json').read_text())
    assert a3['sample_link_mode']=='tcga_participant' and a3['n_aligned_samples']==2

    # 4) unresolved linkage must create HUMAN_REVIEW audit and exit non-zero.
    expr4=pd.DataFrame({'gene':['TP53','ESR1'],'X1':[1,2],'X2':[3,4]})
    clin4=pd.DataFrame({'sample_id':['Y1','Y2'],'age':[50,60]})
    expr4.to_csv(td/'expr4.csv',index=False); clin4.to_csv(td/'clin4.csv',index=False)
    out4=td/'out4'
    run(['--expression',str(td/'expr4.csv'),'--clinical',str(td/'clin4.csv'),'--outdir',str(out4)],expect=2)
    a4=json.loads((out4/'adapter_audit.json').read_text())
    assert a4['status']=='HUMAN_REVIEW' and a4['unresolved_fields']
    assert not (out4/'expression_common_schema.csv').exists()

print('Issue 20 BLCA adapter contract tests: PASS')
