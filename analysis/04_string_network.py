#!/usr/bin/env python3
"""STRING confidence-threshold sensitivity, centrality, rank and resilience exports.

Besides manuscript summaries, this script exports the complete retained gene-gene
edge set and node-level centrality table at every tested STRING threshold so that
all network quantities used downstream are inspectable.
"""
import argparse
from pathlib import Path
import numpy as np, pandas as pd, networkx as nx
from scipy.stats import spearmanr
from common import read_table


def lcc_fraction_original(G, n0):
    """Largest connected component size as a fraction of the original graph size."""
    if n0 <= 0 or G.number_of_nodes() == 0:
        return 0.0
    return len(max(nx.connected_components(G), key=len)) / n0


def _select_target_node(H, mode, rng):
    """Select the next node with deterministic tie-breaking.

    Random removal samples uniformly from lexicographically sorted remaining nodes.
    Degree- and betweenness-targeted attacks are adaptive: centrality is recomputed
    after every deletion and lexicographically smallest node breaks exact ties.
    """
    nodes = sorted(H.nodes(), key=str)
    if mode == 'random':
        return nodes[int(rng.integers(0, len(nodes)))]
    if mode == 'degree':
        scores = dict(H.degree())
    elif mode == 'betweenness':
        scores = nx.betweenness_centrality(H)
    else:
        raise ValueError(f'Unknown attack mode: {mode}')
    best = max(scores.values())
    tied = [n for n in nodes if np.isclose(scores[n], best, rtol=0.0, atol=1e-15)]
    return tied[0]


def attack_curve(G, mode, seed=0, max_removed_fraction=0.5):
    """Return the prespecified node-removal resilience curve.

    x = fraction of *original* nodes removed.
    y = LCC size / original node count.
    The curve is evaluated from x=0 through max_removed_fraction.  When the
    discrete deletion grid crosses the requested boundary, a linearly
    interpolated endpoint is added exactly at the boundary so AUCs are
    comparable for odd/even graph sizes.
    """
    if not (0 < max_removed_fraction <= 1):
        raise ValueError('max_removed_fraction must be in (0, 1].')
    n0 = G.number_of_nodes()
    if n0 == 0:
        return np.array([0.0, max_removed_fraction]), np.array([0.0, 0.0])

    rng = np.random.default_rng(seed)
    H = G.copy()
    xs = [0.0]
    ys = [lcc_fraction_original(H, n0)]

    while H.number_of_nodes() > 0 and xs[-1] < max_removed_fraction:
        node = _select_target_node(H, mode, rng)
        H.remove_node(node)
        xs.append((n0 - H.number_of_nodes()) / n0)
        ys.append(lcc_fraction_original(H, n0))

    # Standardize the right boundary at exactly max_removed_fraction.
    if xs[-1] > max_removed_fraction:
        x1, x2 = xs[-2], xs[-1]
        y1, y2 = ys[-2], ys[-1]
        w = (max_removed_fraction - x1) / (x2 - x1)
        xs[-1] = max_removed_fraction
        ys[-1] = y1 + w * (y2 - y1)
    elif xs[-1] < max_removed_fraction:
        xs.append(max_removed_fraction)
        ys.append(ys[-1])

    return np.asarray(xs, float), np.asarray(ys, float)


def attack_auc(G, mode, seed=0, max_removed_fraction=0.5):
    xs, ys = attack_curve(G, mode, seed=seed, max_removed_fraction=max_removed_fraction)
    return float(np.trapezoid(ys, xs))

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--edges',required=True,help='TSV/CSV with protein1, protein2, combined_score');ap.add_argument('--mapping',required=True,help='Protein-to-gene mapping');ap.add_argument('--genes',required=True,help='Candidate gene list/table');ap.add_argument('--outdir',default='results/string');ap.add_argument('--random-replicates',type=int,default=100,help='Number of random-removal replicates (default: 100)');ap.add_argument('--random-seed-start',type=int,default=0,help='First integer seed for random-removal replicates (default: 0)');ap.add_argument('--attack-max-fraction',type=float,default=0.5,help='Maximum removed-node fraction integrated for resilience AUC (default: 0.5)');args=ap.parse_args();out=Path(args.outdir);out.mkdir(parents=True,exist_ok=True)
    if args.random_replicates < 1: raise ValueError('--random-replicates must be >= 1')
    if not (0 < args.attack_max_fraction <= 1): raise ValueError('--attack-max-fraction must be in (0, 1]')
    e=read_table(args.edges);m=read_table(args.mapping);genes=set(read_table(args.genes).iloc[:,0].astype(str).str.upper());mp=dict(zip(m.iloc[:,0].astype(str),m.iloc[:,1].astype(str).str.upper()));mapped_genes=genes & set(mp.values());e['g1']=e['protein1'].map(mp);e['g2']=e['protein2'].map(mp);e=e[e.g1.isin(mapped_genes)&e.g2.isin(mapped_genes)].copy()
    ranks={};summary=[];graphs={};all_edges=[];all_nodes=[];top20_rows=[]
    for thr in [400,700,900]:
        x=e[pd.to_numeric(e.combined_score)>=thr].copy();G=nx.Graph();G.add_nodes_from(sorted(mapped_genes));G.add_edges_from(zip(x.g1,x.g2));graphs[thr]=G
        deg=dict(G.degree());ranks[thr]=pd.Series(deg).rank(ascending=False,method='average')
        bet=nx.betweenness_centrality(G); clo=nx.closeness_centrality(G)
        node_df=pd.DataFrame({
            'score':thr,'gene':sorted(mapped_genes),
        })
        node_df['degree']=node_df.gene.map(deg).astype(int)
        node_df['degree_rank']=node_df.gene.map(ranks[thr])
        node_df['betweenness']=node_df.gene.map(bet)
        node_df['closeness']=node_df.gene.map(clo)
        node_df.to_csv(out/f'string_node_centrality_{thr}.csv',index=False); all_nodes.append(node_df)
        edge_df=x[['g1','g2','combined_score']].copy().rename(columns={'g1':'gene1','g2':'gene2'})
        edge_df.insert(0,'score',thr);edge_df.to_csv(out/f'string_edges_{thr}.csv',index=False);all_edges.append(edge_df)
        top=node_df.sort_values(['degree_rank','gene']).head(20).copy();top['top20_rank']=np.arange(1,len(top)+1);top20_rows.append(top[['score','top20_rank','gene','degree','degree_rank']])
        summary.append({'score':thr,'nodes':G.number_of_nodes(),'edges':G.number_of_edges(),'density':nx.density(G)})
    pd.DataFrame(summary).to_csv(out/'string_thresholds.csv',index=False)
    pd.concat(all_nodes,ignore_index=True).to_csv(out/'string_node_centrality_all_thresholds.csv',index=False)
    pd.concat(all_edges,ignore_index=True).to_csv(out/'string_edges_all_thresholds.csv',index=False)
    pd.concat(top20_rows,ignore_index=True).to_csv(out/'top20_hubs_by_threshold.csv',index=False)
    rr=[]
    for a,b in [(400,700),(700,900),(400,900)]:
        common=ranks[a].index.intersection(ranks[b].index);rho,_=spearmanr(ranks[a].loc[common],ranks[b].loc[common]);rr.append({'comparison':f'{a} vs {b}','spearman_rho':rho})
    pd.DataFrame(rr).to_csv(out/'degree_rank_stability.csv',index=False)
    top700=set(ranks[700].sort_values().head(20).index);ov=[]
    for thr in [400,700,900]:
        top=set(ranks[thr].sort_values().head(20).index);ov.append({'comparison':f'{thr} vs 700' if thr!=700 else '700 reference','jaccard_overlap':len(top&top700)/len(top|top700)})
    pd.DataFrame(ov).to_csv(out/'top20_overlap.csv',index=False)
    auc=[];rep=[];curve_rows=[]
    for mode in ['random','degree','betweenness']:
        if mode=='random':
            seeds=list(range(args.random_seed_start,args.random_seed_start+args.random_replicates))
        else:
            seeds=[0]
        vals=[]
        for j,seed in enumerate(seeds, start=1):
            xs,ys=attack_curve(graphs[700],mode,seed=seed,max_removed_fraction=args.attack_max_fraction)
            value=float(np.trapezoid(ys,xs)); vals.append(value)
            rep.append({'strategy':mode,'replicate':j,'seed':seed if mode=='random' else np.nan,'auc':value,'max_removed_fraction':args.attack_max_fraction,'lcc_normalization':'original_node_count'})
            curve_rows.extend({'strategy':mode,'replicate':j,'seed':seed if mode=='random' else np.nan,'fraction_removed':float(x),'lcc_fraction_original':float(y)} for x,y in zip(xs,ys))
        auc.append({'strategy':mode,'auc':float(np.mean(vals)),'auc_sd':float(np.std(vals,ddof=1)) if len(vals)>1 else 0.0,'replicates_n':len(vals),'max_removed_fraction':args.attack_max_fraction,'lcc_normalization':'original_node_count','target_recomputed_each_step':mode!='random'})
    pd.DataFrame(auc).to_csv(out/'node_removal_resilience.csv',index=False)
    pd.DataFrame(rep).to_csv(out/'node_removal_resilience_replicates.csv',index=False)
    pd.DataFrame(curve_rows).to_csv(out/'node_removal_resilience_curves.csv',index=False)
    import json
    audit={
        'network_threshold':700,
        'original_nodes':int(graphs[700].number_of_nodes()),
        'original_edges':int(graphs[700].number_of_edges()),
        'lcc_normalization':'largest_connected_component_nodes / original_node_count',
        'x_axis':'removed_nodes / original_node_count',
        'auc_interval':[0.0,float(args.attack_max_fraction)],
        'auc_integration':'trapezoidal with linear interpolation to exact right boundary',
        'random_replicates':int(args.random_replicates),
        'random_seed_start':int(args.random_seed_start),
        'random_seed_end':int(args.random_seed_start+args.random_replicates-1),
        'random_sampling':'uniform over lexicographically sorted remaining nodes',
        'degree_attack':'adaptive degree recomputed after each removal; lexicographic tie-break',
        'betweenness_attack':'adaptive NetworkX betweenness centrality recomputed after each removal; lexicographic tie-break',
    }
    (out/'node_removal_protocol.json').write_text(json.dumps(audit,indent=2)+'\n')
if __name__=='__main__':main()
