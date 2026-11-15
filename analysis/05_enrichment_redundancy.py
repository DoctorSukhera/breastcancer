#!/usr/bin/env python3
"""Reduce FDR-significant GO/KEGG terms by gene-set Jaccard overlap.

The full supplied enrichment result table and the complete FDR-significant subset
are exported before the manuscript's top-term redundancy-reduction step. This
keeps the compact module representation traceable to all input enrichment rows.
"""
import argparse
from pathlib import Path
import pandas as pd, networkx as nx
from common import read_table


def geneset(x): return {g.strip().upper() for g in str(x).replace(';',',').split(',') if g.strip()}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--enrichment',required=True,help='Table with term, source, adjusted_p, genes');ap.add_argument('--top',type=int,default=180);ap.add_argument('--jaccard',type=float,default=.40);ap.add_argument('--outdir',default='results/enrichment');args=ap.parse_args();out=Path(args.outdir);out.mkdir(parents=True,exist_ok=True)
    all_terms=read_table(args.enrichment).copy();all_terms['adjusted_p']=pd.to_numeric(all_terms.adjusted_p,errors='coerce');all_terms['fdr_significant']=all_terms.adjusted_p.lt(.05)
    all_terms.to_csv(out/'enrichment_all_terms.csv',index=False)
    significant=all_terms[all_terms.fdr_significant].sort_values('adjusted_p').copy();significant.to_csv(out/'enrichment_all_significant_terms.csv',index=False)
    d=significant.head(args.top).copy();d['gene_set']=d.genes.map(geneset);G=nx.Graph();G.add_nodes_from(d.index)
    inds=list(d.index)
    for i,a in enumerate(inds):
        A=d.at[a,'gene_set']
        for b in inds[i+1:]:
            B=d.at[b,'gene_set'];u=len(A|B);j=len(A&B)/u if u else 0
            if j>=args.jaccard:G.add_edge(a,b,jaccard=j)
    reps=[];membership=[]
    for mid,comp in enumerate(nx.connected_components(G),1):
        module_id=f'M{mid}';sub=d.loc[list(comp)].sort_values('adjusted_p');r=sub.iloc[0]
        reps.append({'module_id':module_id,'representative_term':r.term,'source':r.source,'adjusted_p':r.adjusted_p,'members_n':len(sub),'genes':r.genes})
        rep_idx=r.name
        for idx,row in sub.iterrows():
            membership.append({'module_id':module_id,'term':row.term,'source':row.source,'adjusted_p':row.adjusted_p,
                               'genes':row.genes,'is_representative':int(idx==rep_idx)})
    pd.DataFrame(reps,columns=['module_id','representative_term','source','adjusted_p','members_n','genes']).to_csv(out/'representative_modules.csv',index=False)
    pd.DataFrame(membership,columns=['module_id','term','source','adjusted_p','genes','is_representative']).to_csv(out/'enrichment_cluster_membership.csv',index=False)
    d.drop(columns='gene_set').to_csv(out/'significant_terms_used_for_clustering.csv',index=False)
    print('Total enrichment rows:',len(all_terms))
    print('FDR-significant terms:',len(significant))
    print('Terms used for clustering:',len(d))
    print('Representative modules:',len(reps))
if __name__=='__main__':main()
