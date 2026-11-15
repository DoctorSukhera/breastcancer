from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
RES=ROOT/'results'/'generated'

src=(ROOT/'benchmark'/'analyze_results.py').read_text().lower()
for forbidden in ['binomtest','wilcoxon','holm_adjust','bootstrap_mean_ci']:
    assert forbidden not in src, forbidden

primary=pd.read_csv(RES/'primary_paired_policy_comparisons.csv')
det=pd.read_csv(RES/'bounded_vs_deterministic_paired_comparison.csv')

# No population-inference columns survive.
for df in [primary,det]:
    forbidden_cols={'p_value','raw_p','holm_p','ci_low','ci_high','test'}
    assert forbidden_cols.isdisjoint(df.columns), forbidden_cols & set(df.columns)
    assert set(df.inference_scope)=={'finite constructed benchmark; descriptive, not population inference'}
    assert (df.n_scenarios==760).all()
    assert (df.n_families==9).all()

# Paired counts account for every frozen scenario.
for _,r in primary.iterrows():
    assert int(r.bounded_better_n+r.tie_n+r.comparator_better_n)==760
for _,r in det.iterrows():
    assert int(r.bounded_better_n+r.tie_n+r.comparator_better_n)==760

# Strong deterministic comparator: differences are localized, not described by tiny P values.
aa=det.set_index('metric').loc['Action appropriateness']
assert abs(float(aa.difference)-0.15789473684210525)<1e-12
assert int(aa.bounded_better_n)==120 and int(aa.tie_n)==640 and int(aa.comparator_better_n)==0

actions=det.set_index('metric').loc['Actions per scenario']
assert abs(float(actions.difference))<1e-15
assert int(actions.tie_n)==760

# Family files are complete and expose heterogeneity directly.
pf=pd.read_csv(RES/'primary_policy_comparisons_by_family.csv')
df=pd.read_csv(RES/'bounded_vs_deterministic_by_family.csv')
assert len(pf)==3*9
assert len(df)==4*9
assert pf.groupby('comparison').family.nunique().eq(9).all()
assert df.groupby('metric').family.nunique().eq(9).all()

print('Issue 12 finite-benchmark statistical interpretation tests: PASS')

fig=pd.read_csv(ROOT/'data'/'source_tables'/'Figure5_paired_policy_comparisons.csv')
assert set(fig.columns)=={'comparison','difference','sensitivity_low','sensitivity_high'}
figsrc=(ROOT/'scripts'/'generate_figures_2_6.py').read_text()
assert 'leave-one-family-out sensitivity range (not a confidence interval)' in figsrc
assert 'd["ci_low"]' not in figsrc and 'd["ci_high"]' not in figsrc
