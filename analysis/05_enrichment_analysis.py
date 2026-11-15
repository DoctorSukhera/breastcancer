#!/usr/bin/env python3
"""Reproducible GO/KEGG over-representation analysis from local gene-set snapshots.

This stage intentionally avoids live Enrichr library discovery.  The original
analysis used GSEApy/Enrichr, but live library names/content can change.  For a
reproducible rerun, users provide explicit local GO Biological Process and KEGG
Human gene-set snapshots (GMT or TSV).  We then compute one-sided
hypergeometric over-representation P values and Benjamini-Hochberg FDR within
each source library.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd
from scipy.stats import hypergeom

from common import bh, read_table


def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def norm_gene(x) -> str:
    return str(x).strip().upper()


def read_genes(path: Path, gene_column: str | None=None) -> list[str]:
    df=read_table(path)
    col=gene_column if gene_column else df.columns[0]
    if col not in df.columns:
        raise ValueError(f"Gene column {col!r} not found in {path}")
    vals=df[col].map(norm_gene)
    return sorted({x for x in vals if x and x not in {'NAN','NONE'}})


def read_gene_sets(path: Path, source: str) -> list[dict]:
    """Read GMT or a two-column TSV/CSV (term, genes)."""
    rows=[]
    if path.suffix.lower()=='.gmt':
        for line in path.read_text(encoding='utf-8').splitlines():
            if not line.strip():
                continue
            parts=line.rstrip('\n').split('\t')
            if len(parts)<3:
                raise ValueError(f'Invalid GMT row in {path}: expected term, description, >=1 gene')
            term=parts[0].strip(); genes={norm_gene(g) for g in parts[2:] if str(g).strip()}
            rows.append({'term':term,'source':source,'geneset':genes})
    else:
        df=read_table(path)
        if not {'term','genes'}.issubset(df.columns):
            raise ValueError(f'{path} must contain columns term, genes (or use GMT)')
        for _,r in df.iterrows():
            genes={norm_gene(g) for g in str(r['genes']).replace(';',',').split(',') if g.strip()}
            rows.append({'term':str(r['term']).strip(),'source':source,'geneset':genes})
    if not rows:
        raise ValueError(f'No gene sets found in {path}')
    return rows


def ora(query: set[str], rows: list[dict], source: str, background: set[str] | None=None) -> pd.DataFrame:
    lib_universe=set().union(*(r['geneset'] for r in rows))
    universe=(set(background)&lib_universe) if background is not None else lib_universe
    q=query & universe
    M=len(universe); N=len(q)
    if M==0 or N==0:
        raise ValueError(f'No query genes overlap the {source} gene-set universe')
    out=[]
    for r in rows:
        gs=r['geneset'] & universe
        n=len(gs); overlap=sorted(q & gs); k=len(overlap)
        p=float(hypergeom.sf(k-1,M,n,N)) if k>0 else 1.0
        out.append({
            'term':r['term'],'source':source,'p_value':p,'adjusted_p':None,
            'overlap_n':k,'query_n':N,'term_size':n,'background_n':M,
            'genes':','.join(overlap),
        })
    d=pd.DataFrame(out)
    d['adjusted_p']=bh(d['p_value'].to_numpy())
    return d.sort_values(['adjusted_p','p_value','term']).reset_index(drop=True)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--genes',required=True,help='Gene list/table used for enrichment (first column)')
    ap.add_argument('--gene-column',help='Gene column in --genes; default first column')
    ap.add_argument('--go-gene-sets',required=True,help='Frozen GO Biological Process snapshot (GMT or term/genes table)')
    ap.add_argument('--kegg-gene-sets',required=True,help='Frozen KEGG Human snapshot (GMT or term/genes table)')
    ap.add_argument('--go-library-name',default='GO_Biological_Process_snapshot')
    ap.add_argument('--kegg-library-name',default='KEGG_Human_snapshot')
    ap.add_argument('--background',help='Optional explicit background gene list; otherwise each library union is used')
    ap.add_argument('--outdir',default='results/enrichment')
    args=ap.parse_args()

    out=Path(args.outdir);out.mkdir(parents=True,exist_ok=True)
    genes_path=Path(args.genes);go_path=Path(args.go_gene_sets);kegg_path=Path(args.kegg_gene_sets)
    query=set(read_genes(genes_path,args.gene_column))
    background=set(read_genes(Path(args.background))) if args.background else None

    go_rows=read_gene_sets(go_path,args.go_library_name)
    kegg_rows=read_gene_sets(kegg_path,args.kegg_library_name)
    go=ora(query,go_rows,args.go_library_name,background)
    kegg=ora(query,kegg_rows,args.kegg_library_name,background)
    combined=pd.concat([go,kegg],ignore_index=True)
    combined.to_csv(out/'enrichment_computed.csv',index=False)

    audit={
        'method':'one-sided hypergeometric over-representation analysis',
        'multiple_testing':'Benjamini-Hochberg within each source library',
        'query_gene_file':str(genes_path.resolve()),
        'query_gene_column':args.gene_column,
        'query_gene_count_input':len(query),
        'background_mode':'explicit_file' if args.background else 'per-library gene-set union',
        'background_file':str(Path(args.background).resolve()) if args.background else None,
        'go_library_name':args.go_library_name,
        'go_gene_set_file':str(go_path.resolve()),
        'go_gene_set_sha256':sha256(go_path),
        'go_terms_tested':len(go),
        'kegg_library_name':args.kegg_library_name,
        'kegg_gene_set_file':str(kegg_path.resolve()),
        'kegg_gene_set_sha256':sha256(kegg_path),
        'kegg_terms_tested':len(kegg),
        'total_terms_tested':len(combined),
        'fdr_lt_0_05':int(pd.to_numeric(combined.adjusted_p,errors='coerce').lt(.05).sum()),
    }
    (out/'enrichment_analysis_audit.json').write_text(json.dumps(audit,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print('GO terms tested:',len(go))
    print('KEGG terms tested:',len(kegg))
    print('Total terms tested:',len(combined))
    print('FDR-significant terms:',audit['fdr_lt_0_05'])

if __name__=='__main__':
    main()
