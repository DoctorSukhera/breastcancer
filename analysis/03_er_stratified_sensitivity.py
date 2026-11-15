#!/usr/bin/env python3
"""ER-stratified directional stability and between-stratum heterogeneity.

Every prespecified candidate is retained in the output table. Missing expression
or inadequate definitive ER strata are represented by an explicit status field
rather than silently dropping the candidate from the audit trail.
"""
import argparse
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import spearmanr, norm
from common import load_expression, read_table, bh


def fisher_z(r): return np.arctanh(np.clip(r,-.999999,.999999))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--expression',required=True);ap.add_argument('--clinical',required=True);ap.add_argument('--candidates',required=True)
    ap.add_argument('--sample-col',default='sample_id');ap.add_argument('--age-col',default='age');ap.add_argument('--er-col',default='ER');ap.add_argument('--gene-column',default=None);ap.add_argument('--out',default='results/er_stratified.csv');args=ap.parse_args()
    expr=load_expression(args.expression,args.gene_column);clin=read_table(args.clinical);clin[args.sample_col]=clin[args.sample_col].astype(str);clin=clin.set_index(args.sample_col)
    cand=read_table(args.candidates).iloc[:,0].astype(str).str.upper().tolist();rows=[]
    for g in cand:
        base={'gene':g,'rho_er_neg':np.nan,'n_er_neg':0,'rho_er_pos':np.nan,'n_er_pos':0,
              'p_heterogeneity':np.nan,'same_direction':np.nan,'status':'not_in_expression'}
        if g not in expr.index:
            rows.append(base); continue
        stats={}
        for label in [0,1]:
            ids=[s for s in expr.columns.astype(str) if s in clin.index and pd.to_numeric(clin.loc[s,args.er_col],errors='coerce')==label]
            age=pd.to_numeric(clin.loc[ids,args.age_col],errors='coerce');y=pd.to_numeric(expr.loc[g,ids],errors='coerce');m=age.notna()&y.notna()
            rho=np.nan
            if int(m.sum())>=3:
                rho,_=spearmanr(age[m],y[m])
            stats[label]=(rho,int(m.sum()))
        r0,n0=stats[0];r1,n1=stats[1]
        base.update({'rho_er_neg':r0,'n_er_neg':n0,'rho_er_pos':r1,'n_er_pos':n1})
        if n0>=4 and n1>=4 and np.isfinite(r0) and np.isfinite(r1):
            se=np.sqrt(1/(n0-3)+1/(n1-3));z=(fisher_z(r1)-fisher_z(r0))/se;phet=2*norm.sf(abs(z))
            base.update({'p_heterogeneity':phet,'same_direction':int(np.sign(r0)==np.sign(r1)),'status':'tested'})
        else:
            base['status']='insufficient_definitive_er_samples'
        rows.append(base)
    out=pd.DataFrame(rows)
    tested=out['status'].eq('tested')
    out['fdr_er_heterogeneity']=np.nan
    if tested.any(): out.loc[tested,'fdr_er_heterogeneity']=bh(out.loc[tested,'p_heterogeneity'])
    Path(args.out).parent.mkdir(parents=True,exist_ok=True);out.to_csv(args.out,index=False)
if __name__=='__main__':main()
