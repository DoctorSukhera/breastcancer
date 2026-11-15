import importlib.util
import json
import math
import subprocess
import sys
from pathlib import Path

import networkx as nx
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'analysis'))
SCRIPT=ROOT/'analysis/04_string_network.py'
spec=importlib.util.spec_from_file_location('string_network',SCRIPT)
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)


def test_complete_graph_auc_uses_original_n_and_half_interval():
    G=nx.complete_graph(['A','B','C','D'])
    x,y=mod.attack_curve(G,'degree',max_removed_fraction=0.5)
    assert list(x)==[0.0,0.25,0.5]
    assert list(y)==[1.0,0.75,0.5]
    assert math.isclose(mod.attack_auc(G,'degree',max_removed_fraction=0.5),0.375,abs_tol=1e-12)


def test_odd_graph_interpolates_exact_half_boundary():
    G=nx.complete_graph(['A','B','C','D','E'])
    x,y=mod.attack_curve(G,'degree',max_removed_fraction=0.5)
    assert math.isclose(x[-1],0.5,abs_tol=1e-12)
    assert math.isclose(y[-1],0.5,abs_tol=1e-12)
    assert math.isclose(mod.attack_auc(G,'degree',max_removed_fraction=0.5),0.375,abs_tol=1e-12)


def test_random_attack_is_insertion_order_independent_for_fixed_seed():
    edges=[('A','B'),('B','C'),('C','D'),('D','E'),('A','E'),('B','D')]
    g1=nx.Graph(); g1.add_nodes_from(['A','B','C','D','E']); g1.add_edges_from(edges)
    g2=nx.Graph(); g2.add_nodes_from(reversed(['A','B','C','D','E'])); g2.add_edges_from(reversed(edges))
    x1,y1=mod.attack_curve(g1,'random',seed=7,max_removed_fraction=0.5)
    x2,y2=mod.attack_curve(g2,'random',seed=7,max_removed_fraction=0.5)
    assert list(x1)==list(x2)
    assert list(y1)==list(y2)


def test_targeted_attacks_are_adaptive_with_deterministic_ties():
    G=nx.path_graph(['A','B','C','D'])
    assert math.isclose(mod.attack_auc(G,'degree',max_removed_fraction=0.5),0.28125,abs_tol=1e-12)
    assert math.isclose(mod.attack_auc(G,'betweenness',max_removed_fraction=0.5),0.3125,abs_tol=1e-12)


def test_cli_exports_protocol_curves_and_replicates(tmp_path):
    mapping=pd.DataFrame({'protein':['pA','pB','pC','pD'],'gene':['A','B','C','D']})
    genes=pd.DataFrame({'gene':['A','B','C','D']})
    edges=pd.DataFrame({
        'protein1':['pA','pB','pC','pA','pB'],
        'protein2':['pB','pC','pD','pD','pD'],
        'combined_score':[900,900,900,700,400],
    })
    mapping.to_csv(tmp_path/'mapping.csv',index=False); genes.to_csv(tmp_path/'genes.csv',index=False); edges.to_csv(tmp_path/'edges.csv',index=False)
    out=tmp_path/'out'
    subprocess.run([sys.executable,str(SCRIPT),'--edges',str(tmp_path/'edges.csv'),'--mapping',str(tmp_path/'mapping.csv'),'--genes',str(tmp_path/'genes.csv'),'--outdir',str(out),'--random-replicates','5'],check=True)
    summary=pd.read_csv(out/'node_removal_resilience.csv')
    reps=pd.read_csv(out/'node_removal_resilience_replicates.csv')
    curves=pd.read_csv(out/'node_removal_resilience_curves.csv')
    audit=json.loads((out/'node_removal_protocol.json').read_text())
    assert set(summary.strategy)=={'random','degree','betweenness'}
    assert int(summary.loc[summary.strategy.eq('random'),'replicates_n'].iloc[0])==5
    assert len(reps[reps.strategy.eq('random')])==5
    assert curves.fraction_removed.max() <= 0.5 + 1e-12
    assert math.isclose(curves.fraction_removed.max(),0.5,abs_tol=1e-12)
    assert audit['lcc_normalization']=='largest_connected_component_nodes / original_node_count'
    assert audit['auc_interval']==[0.0,0.5]
    assert audit['random_replicates']==5
