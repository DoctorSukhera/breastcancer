#!/usr/bin/env python3
"""Directional replication of locked TCGA candidates in GSE42568.

All locked candidates are retained in the exported table. Candidates that cannot
be mapped into the external expression matrix are represented explicitly rather
than silently omitted, allowing the result table to serve as a complete audit of
the prespecified locked set.
"""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from common import read_table, bh


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--series-matrix',required=True,help='Processed GEO expression table: probe x sample')
    ap.add_argument('--annotation',required=True,help='GPL annotation with probe and gene-symbol columns')
    ap.add_argument('--metadata',required=True,help='Sample metadata containing sample ID and age')
    ap.add_argument('--locked',required=True,help='Locked candidate table from 01_tcga_age_association.py')
    ap.add_argument('--probe-col',default='probe_id');ap.add_argument('--symbol-col',default='gene_symbol')
    ap.add_argument('--sample-col',default='sample_id');ap.add_argument('--age-col',default='age')
    ap.add_argument('--out',default='results/external_replication.csv')
    args=ap.parse_args()
    expr=read_table(args.series_matrix);ann=read_table(args.annotation);meta=read_table(args.metadata)
    probe_col=expr.columns[0]
    long=expr.merge(ann[[args.probe_col,args.symbol_col]],left_on=probe_col,right_on=args.probe_col,how='inner')
    long['gene']=long[args.symbol_col].astype(str).str.split('///').str[0].str.strip().str.upper()
    sample_cols=[c for c in expr.columns if c!=probe_col and c in set(meta[args.sample_col].astype(str))]
    gene_expr=long.groupby('gene')[sample_cols].median()
    meta=meta.set_index(args.sample_col).loc[sample_cols]
    age=pd.to_numeric(meta[args.age_col],errors='coerce')
    locked=read_table(args.locked)
    rows=[]
    for _,r in locked.iterrows():
        g=str(r['gene']).upper()
        direction=np.sign(float(r['beta_age_z'])) if pd.notna(r.get('beta_age_z', np.nan)) else np.nan
        base={'gene':g,'mapped_in_geo':int(g in gene_expr.index),'discovery_direction':direction,
              'n':0,'rho_geo':np.nan,'p_directional':np.nan,'status':'not_mapped_to_geo'}
        if g in gene_expr.index:
            y=pd.to_numeric(gene_expr.loc[g],errors='coerce');m=age.notna()&y.notna()
            base['n']=int(m.sum())
            if m.sum()>=3 and np.isfinite(direction):
                rho,p2=spearmanr(age[m],y[m])
                p1=(p2/2) if np.sign(rho)==direction else (1-p2/2)
                base.update({'rho_geo':rho,'p_directional':p1,'status':'tested'})
            else:
                base['status']='insufficient_external_samples'
        rows.append(base)
    out=pd.DataFrame(rows)
    tested=out['status'].eq('tested')
    out['fdr_geo_directional']=np.nan
    if tested.any():
        out.loc[tested,'fdr_geo_directional']=bh(out.loc[tested,'p_directional'])
    out['replicated']=out['fdr_geo_directional'].lt(.05).fillna(False)
    Path(args.out).parent.mkdir(parents=True,exist_ok=True);out.to_csv(args.out,index=False)
    print('Locked candidates:',len(out))
    print('Directional replications at BH-FDR<0.05:',int(out.replicated.sum()))
if __name__=='__main__':main()
