from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]

def test_figure5_reported_matches_source():
    assert (ROOT/'data/source_tables/Figure5_controller_summary.csv').read_bytes()==(ROOT/'results/reported/figure5_controller_summary.csv').read_bytes()

def test_figure6_matches_executable_outputs():
    s=pd.read_csv(ROOT/'data/source_tables/Figure6_ablation_summary.csv').set_index('system')
    g=pd.read_csv(ROOT/'results/generated/ablation_summary_metrics.csv').set_index('system')
    assert s.loc['Provenance removed','provenance']==round(g.loc['Provenance removed','provenance_conformance'],3)
    assert s.loc['Cost-awareness removed','stewardship']==round(g.loc['Cost-awareness removed','resource_stewardship'],3)
    assert s.loc['Cost-awareness removed','stewardship']==0.996

def test_deterministic_reported_matches_generated():
    assert (ROOT/'results/generated/bounded_vs_deterministic_paired_comparison.csv').read_bytes()==(ROOT/'results/reported/bounded_vs_deterministic_paired_comparison.csv').read_bytes()
