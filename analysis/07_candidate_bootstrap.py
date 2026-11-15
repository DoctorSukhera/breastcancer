#!/usr/bin/env python3
"""Bootstrap directional stability for prespecified age-associated candidates.

Resamples subjects with replacement, preserving paired age/expression values, and
reports the distribution of Spearman age-expression correlations. Every supplied
candidate remains in the output table with an explicit status if it cannot be
evaluated.
"""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from common import load_expression, read_table


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--expression',required=True)
    ap.add_argument('--clinical',required=True)
    ap.add_argument('--candidates',required=True,help='Table whose first column contains locked gene symbols')
    ap.add_argument('--sample-col',default='sample_id')
    ap.add_argument('--age-col',default='age')
    ap.add_argument('--gene-column',default=None)
    ap.add_argument('--resamples',type=int,default=1000)
    ap.add_argument('--seed',type=int,default=42)
    ap.add_argument('--out',default='results/candidate_bootstrap.csv')
    args=ap.parse_args()

    expr=load_expression(args.expression,args.gene_column)
    clin=read_table(args.clinical).copy(); clin[args.sample_col]=clin[args.sample_col].astype(str)
    clin=clin.set_index(args.sample_col)
    ids=[s for s in expr.columns.astype(str) if s in clin.index]
    age=pd.to_numeric(clin.loc[ids,args.age_col],errors='coerce').to_numpy()
    genes=read_table(args.candidates).iloc[:,0].astype(str).str.upper().tolist()
    rng=np.random.default_rng(args.seed); rows=[]
    for g in genes:
        base={'gene':g,'n':0,'rho_observed':np.nan,'bootstrap_median':np.nan,'ci_low':np.nan,'ci_high':np.nan,
              'direction_stability':np.nan,'resamples':args.resamples,'seed':args.seed,'status':'not_in_expression'}
        if g not in expr.index:
            rows.append(base); continue
        y=pd.to_numeric(expr.loc[g,ids],errors='coerce').to_numpy(); m=np.isfinite(age)&np.isfinite(y)
        a=age[m]; yy=y[m];base['n']=len(a)
        if len(a)<3:
            base['status']='insufficient_samples';rows.append(base);continue
        obs=float(spearmanr(a,yy).statistic)
        vals=[]
        for _ in range(args.resamples):
            ix=rng.integers(0,len(a),len(a)); vals.append(float(spearmanr(a[ix],yy[ix]).statistic))
        vals=np.asarray(vals,float)
        base.update({'rho_observed':obs,'bootstrap_median':np.nanmedian(vals),
                     'ci_low':np.nanquantile(vals,.025),'ci_high':np.nanquantile(vals,.975),
                     'direction_stability':float(np.mean(np.sign(vals)==np.sign(obs))),'status':'tested'})
        rows.append(base)
    out=pd.DataFrame(rows); Path(args.out).parent.mkdir(parents=True,exist_ok=True); out.to_csv(args.out,index=False)
    print(out.to_string(index=False))
if __name__=='__main__': main()
