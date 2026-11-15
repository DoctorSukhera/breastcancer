#!/usr/bin/env python3
"""TCGA-BRCA curated-gene age association and HC3-adjusted models.

Expected inputs are user-downloaded public data. This script does not download or
redistribute TCGA patient-level files.
"""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
import statsmodels.formula.api as smf
from common import load_expression, read_table, bh


MISSING_CATEGORY_TOKENS = {
    "", "na", "n/a", "nan", "none", "null", "not available",
    "[not available]", "not reported", "[not reported]",
    "not evaluated", "[not evaluated]", "indeterminate",
}


def retain_missing_as_category(series, label="Unknown"):
    """Return a categorical series with missing/placeholder values as `label`.

    The manuscript's adjusted TCGA model treats unavailable receptor/stage
    values as an explicit category rather than deleting those subjects or
    folding them into a biological reference category.
    """
    x = series.copy()
    out = x.astype("string").str.strip()
    low = out.str.lower()
    mask = out.isna() | low.isin(MISSING_CATEGORY_TOKENS)
    out = out.mask(mask, label)
    return out.astype(str)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--expression',required=True,help='Gene x sample log2(UQ-FPKM+1) CSV/TSV; first column gene symbol by default')
    ap.add_argument('--clinical',required=True,help='Clinical CSV/TSV')
    ap.add_argument('--genage',required=True,help='Text/CSV file containing curated gene symbols')
    ap.add_argument('--sample-col',default='sample_id')
    ap.add_argument('--age-col',default='age')
    ap.add_argument('--er-col',default='ER')
    ap.add_argument('--pr-col',default='PR')
    ap.add_argument('--her2-col',default='HER2')
    ap.add_argument('--stage-col',default='stage')
    ap.add_argument('--missing-category-label',default='Unknown',help='Explicit category used for missing ER/PR/HER2/stage values; default: Unknown')
    ap.add_argument('--gene-column',default=None)
    ap.add_argument('--outdir',default='results/molecular_tcga')
    args=ap.parse_args()
    out=Path(args.outdir);out.mkdir(parents=True,exist_ok=True)
    expr=load_expression(args.expression,args.gene_column)
    clin=read_table(args.clinical).copy()
    clin[args.sample_col]=clin[args.sample_col].astype(str)
    covariates=[args.er_col,args.pr_col,args.her2_col,args.stage_col]
    missing_summary=[]
    for c in covariates:
        if c not in clin.columns:
            raise KeyError(f"Required clinical covariate column not found: {c}")
        before=clin[c]
        normalized=retain_missing_as_category(before,args.missing_category_label)
        missing_n=int((normalized == args.missing_category_label).sum())
        clin[c]=normalized
        missing_summary.append({
            'covariate':c,
            'explicit_missing_category':args.missing_category_label,
            'n_explicit_missing_category':missing_n,
            'n_total_clinical_rows':len(clin),
        })
    samples=[s for s in expr.columns.astype(str) if s in set(clin[args.sample_col])]
    expr=expr.loc[:,samples]
    clin=clin.set_index(args.sample_col).loc[samples].reset_index()
    pd.DataFrame([
        {
            'covariate':c,
            'explicit_missing_category':args.missing_category_label,
            'n_explicit_missing_category':int((clin[c] == args.missing_category_label).sum()),
            'n_matched_samples':len(clin),
        }
        for c in covariates
    ]).to_csv(out/'tcga_covariate_missingness_summary.csv',index=False)
    # genage list: accept one-column txt/csv or first column
    try:
        gg=read_table(args.genage).iloc[:,0].astype(str)
    except Exception:
        gg=pd.Series([x.strip() for x in Path(args.genage).read_text().splitlines() if x.strip()])
    genes=sorted(set(gg.str.upper()) & set(expr.index))
    rows=[]
    for g in genes:
        y=pd.to_numeric(expr.loc[g],errors='coerce').to_numpy()
        age=pd.to_numeric(clin[args.age_col],errors='coerce').to_numpy()
        m=np.isfinite(y)&np.isfinite(age)
        rho,p=spearmanr(age[m],y[m]) if m.sum()>=3 else (np.nan,np.nan)
        rows.append({'gene':g,'n':int(m.sum()),'rho_age':rho,'p_age':p})
    unadj=pd.DataFrame(rows);unadj['fdr_age']=bh(unadj.p_age)
    unadj.to_csv(out/'tcga_unadjusted_age_association.csv',index=False)

    adjusted=[]; quadratic=[]
    for g in genes:
        d=clin[[args.age_col,args.er_col,args.pr_col,args.her2_col,args.stage_col]].copy()
        d['expr']=pd.to_numeric(expr.loc[g].reindex(samples).to_numpy(),errors='coerce')
        d['age_z']=(pd.to_numeric(d[args.age_col],errors='coerce')-pd.to_numeric(d[args.age_col],errors='coerce').mean())/pd.to_numeric(d[args.age_col],errors='coerce').std(ddof=0)
        # Missing receptor/stage values have already been encoded as the explicit
        # Unknown category. Complete-case deletion is therefore limited to the
        # outcome and age term, not the categorical clinicopathological covariates.
        d=d.dropna(subset=['expr','age_z'])
        if len(d)<20: continue
        formula=f"expr ~ age_z + C({args.er_col}) + C({args.pr_col}) + C({args.her2_col}) + C({args.stage_col})"
        fit=smf.ols(formula,d).fit(cov_type='HC3')
        adjusted.append({'gene':g,'n':len(d),'beta_age_z':fit.params.get('age_z',np.nan),'ci_low':fit.conf_int().loc['age_z',0],'ci_high':fit.conf_int().loc['age_z',1],'p_age_adjusted':fit.pvalues.get('age_z',np.nan)})
        d['age_z2']=d.age_z**2
        qfit=smf.ols(formula.replace('age_z +','age_z + age_z2 +'),d).fit(cov_type='HC3')
        quadratic.append({'gene':g,'beta_age_z2':qfit.params.get('age_z2',np.nan),'p_age_z2':qfit.pvalues.get('age_z2',np.nan)})
    adj=pd.DataFrame(adjusted);adj['fdr_adjusted']=bh(adj.p_age_adjusted);adj=adj.sort_values('fdr_adjusted')
    adj.to_csv(out/'tcga_adjusted_age_association.csv',index=False)
    q=pd.DataFrame(quadratic);q['fdr_age_z2']=bh(q.p_age_z2);q.to_csv(out/'tcga_quadratic_age_sensitivity.csv',index=False)
    adj.head(40).to_csv(out/'locked_top40_candidates.csv',index=False)
    print('Covariate missing-data rule: explicit category =',args.missing_category_label)
    print('Expression-testable curated genes:',len(genes))
    print('Unadjusted FDR<0.05:',int((unadj.fdr_age<.05).sum()))
    print('Adjusted FDR<0.05:',int((adj.fdr_adjusted<.05).sum()))

if __name__=='__main__': main()
