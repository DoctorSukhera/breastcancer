from pathlib import Path
import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests


def read_table(path):
    path=Path(path)
    sep='\t' if path.suffix.lower() in {'.tsv','.txt'} else ','
    return pd.read_csv(path,sep=sep)


def bh(pvalues):
    p=np.asarray(pvalues,dtype=float)
    out=np.full(len(p),np.nan)
    mask=np.isfinite(p)
    if mask.any(): out[mask]=multipletests(p[mask],method='fdr_bh')[1]
    return out


def load_expression(path, gene_column=None):
    """Return gene x sample numeric expression matrix."""
    df=read_table(path)
    if gene_column is None:
        gene_column=df.columns[0]
    genes=df[gene_column].astype(str).str.upper().str.strip()
    mat=df.drop(columns=[gene_column]).apply(pd.to_numeric,errors='coerce')
    mat.index=genes
    mat=mat.groupby(level=0).median()
    return mat
