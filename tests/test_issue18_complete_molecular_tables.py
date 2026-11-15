import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
COMPILER=ROOT/'analysis'/'08_compile_molecular_tables.py'

with tempfile.TemporaryDirectory() as td:
    r=Path(td);(r/'01_tcga').mkdir();(r/'04_string').mkdir();(r/'05_enrichment').mkdir()
    pd.DataFrame([
        {'gene':'G1','n':30,'rho_age':.5,'p_age':.001,'fdr_age':.002},
        {'gene':'G2','n':30,'rho_age':-.4,'p_age':.01,'fdr_age':.02},
    ]).to_csv(r/'01_tcga/tcga_unadjusted_age_association.csv',index=False)
    pd.DataFrame([
        {'gene':'G1','n':30,'beta_age_z':.2,'ci_low':.1,'ci_high':.3,'p_age_adjusted':.001,'fdr_adjusted':.002},
        {'gene':'G2','n':30,'beta_age_z':-.1,'ci_low':-.2,'ci_high':0,'p_age_adjusted':.02,'fdr_adjusted':.04},
    ]).to_csv(r/'01_tcga/tcga_adjusted_age_association.csv',index=False)
    pd.DataFrame([
        {'gene':'G1','beta_age_z2':.01,'p_age_z2':.4,'fdr_age_z2':.8},
        {'gene':'G2','beta_age_z2':-.01,'p_age_z2':.6,'fdr_age_z2':.8},
    ]).to_csv(r/'01_tcga/tcga_quadratic_age_sensitivity.csv',index=False)
    pd.DataFrame([
        {'gene':'G1','n':30,'beta_age_z':.2,'ci_low':.1,'ci_high':.3,'p_age_adjusted':.001,'fdr_adjusted':.002},
        {'gene':'G2','n':30,'beta_age_z':-.1,'ci_low':-.2,'ci_high':0,'p_age_adjusted':.02,'fdr_adjusted':.04},
    ]).to_csv(r/'01_tcga/locked_top40_candidates.csv',index=False)
    pd.DataFrame([{'covariate':'ER','explicit_missing_category':'Unknown','n_explicit_missing_category':1,'n_matched_samples':30}]).to_csv(r/'01_tcga/tcga_covariate_missingness_summary.csv',index=False)

    pd.DataFrame([
        {'gene':'G1','mapped_in_geo':1,'discovery_direction':1,'n':12,'rho_geo':.4,'p_directional':.01,'status':'tested','fdr_geo_directional':.02,'replicated':True},
        {'gene':'G2','mapped_in_geo':0,'discovery_direction':-1,'n':0,'rho_geo':None,'p_directional':None,'status':'not_mapped_to_geo','fdr_geo_directional':None,'replicated':False},
    ]).to_csv(r/'02_external_replication.csv',index=False)
    pd.DataFrame([
        {'gene':'G1','rho_er_neg':.3,'n_er_neg':12,'rho_er_pos':.4,'n_er_pos':15,'p_heterogeneity':.7,'same_direction':1,'status':'tested','fdr_er_heterogeneity':.8},
        {'gene':'G2','rho_er_neg':-.2,'n_er_neg':12,'rho_er_pos':-.1,'n_er_pos':15,'p_heterogeneity':.6,'same_direction':1,'status':'tested','fdr_er_heterogeneity':.8},
    ]).to_csv(r/'03_er_stratified.csv',index=False)
    pd.DataFrame([
        {'gene':'G1','n':30,'rho_observed':.5,'bootstrap_median':.5,'ci_low':.2,'ci_high':.7,'direction_stability':1.0,'resamples':5,'seed':7,'status':'tested'},
        {'gene':'G2','n':30,'rho_observed':-.4,'bootstrap_median':-.4,'ci_low':-.7,'ci_high':-.1,'direction_stability':1.0,'resamples':5,'seed':7,'status':'tested'},
    ]).to_csv(r/'07_candidate_bootstrap.csv',index=False)

    nodes=[]
    for score in [400,700,900]:
        for g,d in [('G1',1),('G2',1)]: nodes.append({'score':score,'gene':g,'degree':d,'degree_rank':1.5,'betweenness':0,'closeness':1})
    pd.DataFrame(nodes).to_csv(r/'04_string/string_node_centrality_all_thresholds.csv',index=False)
    pd.DataFrame([x for x in nodes if x['score']==700]).to_csv(r/'04_string/string_node_centrality_700.csv',index=False)
    pd.DataFrame([{'score':s,'gene1':'G1','gene2':'G2','combined_score':900} for s in [400,700,900]]).to_csv(r/'04_string/string_edges_all_thresholds.csv',index=False)
    pd.DataFrame([{'strategy':'random','replicate':1,'seed':0,'auc':.3},{'strategy':'degree','replicate':1,'seed':None,'auc':.2}]).to_csv(r/'04_string/node_removal_resilience_replicates.csv',index=False)
    pd.DataFrame([{'strategy':'random','replicate':1,'seed':0,'fraction_removed':0.0,'lcc_fraction_original':1.0},{'strategy':'random','replicate':1,'seed':0,'fraction_removed':0.5,'lcc_fraction_original':0.3}]).to_csv(r/'04_string/node_removal_resilience_curves.csv',index=False)
    (r/'04_string/node_removal_protocol.json').write_text('{"network_threshold":700,"auc_interval":[0.0,0.5]}\n')
    pd.DataFrame([{'score':700,'top20_rank':1,'gene':'G1','degree':1,'degree_rank':1.5}]).to_csv(r/'04_string/top20_hubs_by_threshold.csv',index=False)

    pd.DataFrame([
        {'term':'T1','source':'GO','adjusted_p':.001,'genes':'G1,G2','fdr_significant':True},
        {'term':'T2','source':'KEGG','adjusted_p':.2,'genes':'G2','fdr_significant':False},
    ]).to_csv(r/'05_enrichment/enrichment_all_terms.csv',index=False)
    pd.DataFrame([{'term':'T1','source':'GO','adjusted_p':.001,'genes':'G1,G2','fdr_significant':True}]).to_csv(r/'05_enrichment/enrichment_all_significant_terms.csv',index=False)
    pd.DataFrame([{'module_id':'M1','term':'T1','source':'GO','adjusted_p':.001,'genes':'G1,G2','is_representative':1}]).to_csv(r/'05_enrichment/enrichment_cluster_membership.csv',index=False)
    pd.DataFrame([{'permutation':1,'significant_genes':0},{'permutation':2,'significant_genes':1}]).to_csv(r/'06_permutation_counts.csv',index=False)
    (r/'06_permutation_summary.json').write_text(json.dumps({'strata_columns':['ER'],'n_permutations':2}))

    run=subprocess.run([sys.executable,str(COMPILER),'--molecular-dir',str(r)],cwd=ROOT,capture_output=True,text=True)
    assert run.returncode==0, run.stderr+'\n'+run.stdout
    tab=r/'08_complete_tables'
    m1=pd.read_csv(tab/'M1_tcga_all_curated_gene_statistics.csv'); assert len(m1)==2
    m2=pd.read_csv(tab/'M2_locked_candidates_complete_multi_evidence.csv'); assert len(m2)==2
    assert {'rho_geo','rho_er_pos','direction_stability','string_degree_700'}.issubset(m2.columns)
    assert len(pd.read_csv(tab/'M3_string_node_metrics_all_thresholds.csv'))==6
    assert len(pd.read_csv(tab/'M4_string_edges_all_thresholds.csv'))==3
    assert len(pd.read_csv(tab/'M5_enrichment_all_terms.csv'))==2
    assert len(pd.read_csv(tab/'M6_enrichment_cluster_membership.csv'))==1
    assert len(pd.read_csv(tab/'M7_permutation_null_distribution.csv'))==2
    inv=pd.read_csv(tab/'M8_molecular_result_table_inventory.csv'); assert inv.sha256.str.len().eq(64).all()
    manifest=json.loads((tab/'MOLECULAR_RESULT_TABLES_MANIFEST.json').read_text())
    assert manifest['status']=='complete' and manifest['row_counts']['M1_tcga_all_curated_gene_statistics']==2
    for p in tab.glob('M[1-7]_*.csv'):
        cols={c.lower() for c in pd.read_csv(p,nrows=0).columns};assert 'sample_id' not in cols and 'patient_id' not in cols

src=(ROOT/'analysis/04_string_network.py').read_text();assert 'string_node_centrality_all_thresholds.csv' in src and 'string_edges_all_thresholds.csv' in src
assert 'enrichment_all_terms.csv' in (ROOT/'analysis/05_enrichment_redundancy.py').read_text()
assert 'analysis/08_compile_molecular_tables.py' in (ROOT/'analysis/run_molecular_pipeline.py').read_text()
print('Issue 18 complete molecular result-table tests: PASS')
