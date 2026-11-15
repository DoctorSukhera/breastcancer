#!/usr/bin/env python3
"""Compile complete derived molecular result tables from pipeline stage outputs.

This compiler operates only on derived, gene-/term-/network-level outputs. It
never exports subject-level TCGA or GEO records. The goal is to provide a
reviewer-auditable table package underlying manuscript summaries and figures.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()


def read(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def write(df: pd.DataFrame, path: Path) -> Path:
    path.parent.mkdir(parents=True,exist_ok=True)
    df.to_csv(path,index=False)
    return path


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--molecular-dir',required=True,help='Root output directory created by run_molecular_pipeline.py')
    ap.add_argument('--outdir',default=None,help='Output table directory; default <molecular-dir>/08_complete_tables')
    args=ap.parse_args()
    root=Path(args.molecular_dir).expanduser().resolve()
    out=Path(args.outdir).expanduser().resolve() if args.outdir else root/'08_complete_tables'
    out.mkdir(parents=True,exist_ok=True)

    # M1: every expression-testable curated gene and every primary statistic.
    u=read(root/'01_tcga/tcga_unadjusted_age_association.csv')
    a=read(root/'01_tcga/tcga_adjusted_age_association.csv')
    q=read(root/'01_tcga/tcga_quadratic_age_sensitivity.csv')
    m1=u.merge(a,on='gene',how='outer',suffixes=('_unadjusted','_adjusted')).merge(q,on='gene',how='outer')
    m1['unadjusted_fdr_lt_0_05']=pd.to_numeric(m1.get('fdr_age'),errors='coerce').lt(.05)
    m1['adjusted_fdr_lt_0_05']=pd.to_numeric(m1.get('fdr_adjusted'),errors='coerce').lt(.05)
    m1['quadratic_fdr_lt_0_05']=pd.to_numeric(m1.get('fdr_age_z2'),errors='coerce').lt(.05)
    m1=m1.sort_values(['fdr_adjusted','fdr_age','gene'],na_position='last')
    p1=write(m1,out/'M1_tcga_all_curated_gene_statistics.csv')

    # M2: every locked candidate across all downstream evidence layers.
    locked=read(root/'01_tcga/locked_top40_candidates.csv')
    ext=read(root/'02_external_replication.csv')
    er=read(root/'03_er_stratified.csv')
    boot=read(root/'07_candidate_bootstrap.csv')
    c700=read(root/'04_string/string_node_centrality_700.csv')
    c700=c700.drop(columns=['score'],errors='ignore').rename(columns={
        'degree':'string_degree_700','degree_rank':'string_degree_rank_700',
        'betweenness':'string_betweenness_700','closeness':'string_closeness_700'})
    m2=(locked.merge(ext,on='gene',how='left',suffixes=('','_external'))
              .merge(er,on='gene',how='left',suffixes=('','_er'))
              .merge(boot,on='gene',how='left',suffixes=('','_bootstrap'))
              .merge(c700,on='gene',how='left'))
    if 'same_direction' in m2.columns and 'fdr_er_heterogeneity' in m2.columns:
        m2['er_robust_by_prespecified_rule']=(pd.to_numeric(m2['same_direction'],errors='coerce').eq(1) &
            pd.to_numeric(m2['fdr_er_heterogeneity'],errors='coerce').ge(.05))
    m2['locked_rank']=np.arange(1,len(m2)+1)
    p2=write(m2,out/'M2_locked_candidates_complete_multi_evidence.csv')

    # M3/M4: all STRING node and retained edge data at all tested thresholds.
    m3=read(root/'04_string/string_node_centrality_all_thresholds.csv')
    p3=write(m3,out/'M3_string_node_metrics_all_thresholds.csv')
    m4=read(root/'04_string/string_edges_all_thresholds.csv')
    p4=write(m4,out/'M4_string_edges_all_thresholds.csv')

    # M5/M6: full enrichment universe supplied to the redundancy-reduction stage
    # and exact top-term-to-module membership used for representative selection.
    m5=read(root/'05_enrichment/enrichment_all_terms.csv')
    p5=write(m5,out/'M5_enrichment_all_terms.csv')
    m6=read(root/'05_enrichment/enrichment_cluster_membership.csv')
    p6=write(m6,out/'M6_enrichment_cluster_membership.csv')

    # M7: complete finite permutation-null distribution (all permutations).
    m7=read(root/'06_permutation_counts.csv')
    p7=write(m7,out/'M7_permutation_null_distribution.csv')

    # M8: table-level provenance inventory. Include both compiled tables and
    # important stage-level full outputs not duplicated above.
    files=[
        (p1,'All curated-gene unadjusted, adjusted and quadratic age statistics'),
        (p2,'All locked candidates across external replication, ER sensitivity, bootstrap and STRING score-700 evidence'),
        (p3,'All STRING candidate-node metrics at thresholds 400, 700 and 900'),
        (p4,'All retained STRING gene-gene edges at thresholds 400, 700 and 900'),
        (p5,'All enrichment rows supplied to the enrichment stage, with FDR-significance flag'),
        (p6,'Exact top-term clustering membership and representative-term flags'),
        (p7,'All stratified age-label permutation null counts'),
        (root/'05_enrichment/enrichment_all_significant_terms.csv','Complete FDR-significant enrichment subset'),
        (root/'04_string/node_removal_resilience_replicates.csv','All random-removal AUC replicates plus deterministic targeted-removal AUCs'),
        (root/'04_string/node_removal_resilience_curves.csv','All node-removal resilience curve points (LCC normalized to original node count)'),
        (root/'04_string/node_removal_protocol.json','Machine-readable node-removal normalization, AUC interval, seed and targeting protocol'),
        (root/'04_string/top20_hubs_by_threshold.csv','Top-20 degree hubs at each STRING threshold'),
        (root/'06_permutation_summary.json','Permutation design and empirical-P audit metadata'),
        (root/'01_tcga/tcga_covariate_missingness_summary.csv','TCGA covariate missingness audit'),
    ]
    inv=[]
    for path,desc in files:
        if not path.is_file():
            raise FileNotFoundError(path)
        if path.suffix.lower()=='.csv':
            df=pd.read_csv(path); rows=len(df); cols=len(df.columns); colnames='|'.join(map(str,df.columns))
        else:
            rows=np.nan; cols=np.nan; colnames=''
        inv.append({'file':str(path.relative_to(root)) if path.is_relative_to(root) else str(path),
                    'description':desc,'rows':rows,'columns_n':cols,'column_names':colnames,
                    'sha256':sha256(path)})
    p8=write(pd.DataFrame(inv),out/'M8_molecular_result_table_inventory.csv')

    manifest={
        'status':'complete',
        'scope':'derived molecular result tables only; no subject-level TCGA/GEO records',
        'tables':{
            'M1_tcga_all_curated_gene_statistics':str(p1),
            'M2_locked_candidates_complete_multi_evidence':str(p2),
            'M3_string_node_metrics_all_thresholds':str(p3),
            'M4_string_edges_all_thresholds':str(p4),
            'M5_enrichment_all_terms':str(p5),
            'M6_enrichment_cluster_membership':str(p6),
            'M7_permutation_null_distribution':str(p7),
            'M8_molecular_result_table_inventory':str(p8),
        },
        'row_counts':{p.stem:int(len(pd.read_csv(p))) for p in [p1,p2,p3,p4,p5,p6,p7,p8]},
        'sha256':{p.name:sha256(p) for p in [p1,p2,p3,p4,p5,p6,p7,p8]},
    }
    (out/'MOLECULAR_RESULT_TABLES_MANIFEST.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print('Complete derived molecular table package:',out)
    for p in [p1,p2,p3,p4,p5,p6,p7,p8]:
        print(p.name, len(pd.read_csv(p)), 'rows')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
