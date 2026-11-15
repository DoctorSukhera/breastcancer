import csv, inspect, json, sys
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'/'frozen'; RES=ROOT/'results'/'generated'
sys.path.insert(0,str(ROOT/'benchmark'))
import controller as controller_module
from controller import BoundedController, StaticWorkflow, GoalPlanner, AdaptivePlanner, DeterministicErrorHandlingWorkflow, RunState, _apply_action
from evaluator import evaluate_run, assess_action_appropriateness
from oracle import oracle_cost, oracle_trace

ctrl=pd.read_csv(DATA/'controller_input_manifest.csv').fillna('')
ref=pd.read_csv(DATA/'reference_policy.csv').fillna('')
refmap={int(r.scenario_id):r.to_dict() for _,r in ref.iterrows()}
joined=ctrl.merge(ref[['scenario_id','family','reference_outcome']],on='scenario_id',validate='one_to_one')

# Issue 1: rule-based balanced construction.
builder=(ROOT/'benchmark'/'build_frozen_inputs.py').read_text().lower()
for phrase in ['reproduces the retained revision action-count summary','goal_counts = {','full_complete_ids[:83]']:
    assert phrase not in builder
canonical=set(json.loads((DATA/'canonical_goal_definitions.json').read_text()))
heldout=set(json.loads((DATA/'heldout_goal_definitions.json').read_text()))
for family,g in joined.groupby('family'):
    counts=g.goal_name.value_counts().to_dict()
    if family=='unseen_composition': assert set(counts)==heldout and set(counts.values())=={12}
    else: assert set(counts)==canonical and len(set(counts.values()))==1

# Issue 2: family/reference isolation.
assert 'family' not in ctrl.columns and 'family' in ref.columns
forbidden={'family','reference_outcome','required_artifacts','require_verification','require_provenance','require_human_review','require_safe_block'}
assert forbidden.isdisjoint(ctrl.columns)
for _,row in ctrl.iterrows():
    s=row.to_dict(); s['scenario_id']=int(s['scenario_id'])
    a=dict(s); a['family']='clean'; b=dict(s); b['family']='prohibited_clinical_request'
    for c in [StaticWorkflow(),GoalPlanner(),AdaptivePlanner(),BoundedController(),DeterministicErrorHandlingWorkflow()]:
        x=c.run(a); y=c.run(b)
        sig=lambda z:(tuple(z.action_trace),z.actual_outcome,z.provenance_ok,z.escalated,z.safe_block,z.failed_attempts,z.stopping_reason)
        assert sig(x)==sig(y),(s['scenario_id'],c.name)

# Issue 3: genuine baseline algorithms, no support-mask class.
src=inspect.getsource(controller_module)
assert 'class BaselineController' not in src and 'def _supported' not in src and 'self.level' not in src

# Issue 4: held-out compositions are genuinely sequence-disjoint and registered.
can=json.loads((DATA/'canonical_goal_definitions.json').read_text()); ho=json.loads((DATA/'heldout_goal_definitions.json').read_text())
assert {tuple(v['sequence']) for v in can.values()}.isdisjoint({tuple(v['sequence']) for v in ho.values()})
with open(DATA/'action_registry.csv') as f: registered={r['action_id'] for r in csv.DictReader(f)}
for name,spec in ho.items(): assert set(spec['sequence']).issubset(registered),name
assert 'unseen_composition' not in src
for name in ho: assert name not in src

# Issue 5: executable action-registry semantics.
with open(DATA/'action_registry.csv') as f: registry={r['action_id']:r for r in csv.DictReader(f)}
assert set(next(csv.DictReader(open(DATA/'action_registry.csv'))).keys())=={'action_id','normalized_cost','prerequisites','produces','category','prohibited_in_clinical_request'}
st=RunState('test'); ok,why=_apply_action(st,'age_association',scenario={'prohibited_pattern':''})
assert not ok and why=='missing_prerequisite' and st.prerequisite_violations==1

# Issue 6: oracle source is controller-independent.
osrc=(ROOT/'benchmark'/'oracle.py').read_text()
assert 'from controller' not in osrc and 'RunState' not in osrc

# Issue 7: stewardship is evaluator/oracle-derived throughout active runners.
for fname in ['run_benchmark.py','run_deterministic_baseline.py','run_ablation.py']:
    text=(ROOT/'benchmark'/fname).read_text()
    assert "['resource_stewardship']=1.0" not in text
    assert 'oracle=base.actual_cost' not in text
bench=pd.read_csv(RES/'benchmark_trajectory_level.csv')
assert bench.resource_stewardship.notna().all()

# Issue 8: transient retry/fallback semantics exactly match independent oracle.
bounded=BoundedController()
trans=joined[joined.family.eq('transient_failure')]
assert len(trans)==120
retry_n=fallback_n=0
for _,row in trans.iterrows():
    sid=int(row.scenario_id); s=ctrl[ctrl.scenario_id.eq(sid)].iloc[0].to_dict(); s['scenario_id']=sid; r=refmap[sid]
    state=bounded.run(s); otr=oracle_trace(s,r)
    assert state.action_trace==otr,(sid,s['transient_mode'],state.action_trace,otr)
    assert abs(state.actual_cost-oracle_cost(s,r))<1e-12
    if s['transient_mode']=='retry':
        retry_n+=1; assert state.action_trace.count('expression_gdc')==2; assert 'expression_cache' not in state.action_trace
    elif s['transient_mode']=='fallback':
        fallback_n+=1; assert state.action_trace.count('expression_gdc')==1; assert state.action_trace.count('expression_cache')==1
    else: raise AssertionError(s['transient_mode'])
assert retry_n==60 and fallback_n==60

# Stronger global consequence: bounded actual cost equals independent oracle in all 760 cases.
b=bench[bench.system.eq('Bounded controller')]
assert len(b)==760
assert (b.actual_cost-b.oracle_cost).abs().max()<1e-12
assert (b.resource_stewardship-1.0).abs().max()<1e-12
assert abs(b.actual_cost.mean()-4.828947368421052)<1e-12

# Issue 9: action appropriateness is sequence-aware, not set-membership-only.
clean_sid=int(ref.loc[ref.family.eq('clean'),'scenario_id'].iloc[0])
cs=ctrl[ctrl.scenario_id.eq(clean_sid)].iloc[0].to_dict(); cs['scenario_id']=clean_sid; cr=refmap[clean_sid]
expected=oracle_trace(cs,cr)
exact=RunState('test'); exact.action_trace=list(expected)
assert assess_action_appropriateness(cs,cr,exact)['appropriate']==1
wrong=RunState('test'); wrong.action_trace=list(expected); wrong.action_trace[0],wrong.action_trace[1]=wrong.action_trace[1],wrong.action_trace[0]
assert set(wrong.action_trace)==set(expected)
assert assess_action_appropriateness(cs,cr,wrong)['appropriate']==0
dup=RunState('test'); dup.action_trace=[expected[0],expected[0]]+expected[1:]
assert assess_action_appropriateness(cs,cr,dup)['appropriate']==0

print('Integrity regression tests for Issues 1-9: PASS')
