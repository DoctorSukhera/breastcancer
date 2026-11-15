from pathlib import Path
import inspect, sys
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'/'frozen'; RES=ROOT/'results'/'generated'
sys.path.insert(0,str(ROOT/'benchmark'))
import controller as controller_module
from controller import BoundedController, DeterministicErrorHandlingWorkflow
from oracle import oracle_trace

inputs=pd.read_csv(DATA/'controller_input_manifest.csv').fillna('')
refs=pd.read_csv(DATA/'reference_policy.csv').fillna('')
joined=inputs.merge(refs[['scenario_id','family','reference_outcome']],on='scenario_id',validate='one_to_one')
refmap={int(r.scenario_id):r.to_dict() for _,r in refs.iterrows()}

def runtime(sid):
    s=inputs[inputs.scenario_id.eq(int(sid))].iloc[0].to_dict(); s['scenario_id']=int(sid); return s

# 1) Comparator source must not force every feasible task to full_prioritization.
src=inspect.getsource(DeterministicErrorHandlingWorkflow)
assert "full['goal_name']='full_prioritization'" not in src
assert 'include_audit=True' not in src

# 2) On clean scenarios, the comparator executes the requested goal exactly.
det=DeterministicErrorHandlingWorkflow(); bounded=BoundedController()
clean=joined[joined.family.eq('clean')]
for _,row in clean.iterrows():
    sid=int(row.scenario_id); s=runtime(sid); r=refmap[sid]
    st=det.run(s)
    assert st.action_trace==oracle_trace(s,r),(sid,s['goal_name'],st.action_trace,oracle_trace(s,r))
    assert st.actual_outcome=='COMPLETE'

# 3) Known pre-execution outage gets the registered fallback, not failure/full workflow.
outage=joined[joined.family.eq('known_source_outage')]
for _,row in outage.iterrows():
    sid=int(row.scenario_id); s=runtime(sid); st=det.run(s)
    assert st.actual_outcome=='COMPLETE'
    assert 'expression_cache' in st.action_trace and 'expression_gdc' not in st.action_trace

# 4) Runtime policy is genuinely conventional retry-once, irrespective of bounded mode.
trans=joined[joined.family.eq('transient_failure')]
retry=fallback=0
for _,row in trans.iterrows():
    sid=int(row.scenario_id); s=runtime(sid); st=det.run(s)
    assert st.actual_outcome=='COMPLETE'
    assert st.action_trace.count('expression_gdc')==2
    assert 'expression_cache' not in st.action_trace
    if s['transient_mode']=='retry':
        retry += 1; assert st.action_trace==oracle_trace(s,refmap[sid])
    else:
        fallback += 1; assert st.action_trace!=oracle_trace(s,refmap[sid])
assert retry==60 and fallback==60

# 5) Comparator deliberately lacks cost-aware optimization but remains scientifically valid.
rs=joined[joined.family.eq('resource_stress')]
for _,row in rs.iterrows():
    sid=int(row.scenario_id); s=runtime(sid); st=det.run(s)
    assert st.actual_outcome=='COMPLETE'
    assert 'expression_gdc' in st.action_trace and 'expression_cache' not in st.action_trace

# 6) Provenance repair is performed without an unconditional audit action.
prov=joined[joined.family.eq('provenance_attack')]
for _,row in prov.iterrows():
    sid=int(row.scenario_id); s=runtime(sid); st=det.run(s)
    assert 'provenance_repair' in st.action_trace
    assert 'audit_log' not in st.action_trace
    assert st.provenance_ok

# 7) Endpoint governance remains strong.
out=pd.read_csv(RES/'deterministic_error_handling_trajectory_level.csv')
assert len(out)==760
assert out.policy_conformance.mean()==1.0
assert out.safety_conformance.mean()==1.0
assert out.provenance_conformance.mean()==1.0
assert out.escalation_conformance.mean()==1.0
assert abs(out.action_appropriateness.mean()-0.8421052631578947)<1e-12
assert abs(out.resource_stewardship.mean()-0.9926196881157217)<1e-12
assert abs(out.actual_cost.mean()-4.868421052631579)<1e-12

# 8) Equal action count with bounded is a real no-difference result, not NaN.
b=bounded
for _,row in inputs.iterrows():
    s=row.to_dict(); s['scenario_id']=int(s['scenario_id'])
    assert det.run(s).actions_n==b.run(s).actions_n
paired=pd.read_csv(RES/'bounded_vs_deterministic_paired_comparison.csv').set_index('metric')
a=paired.loc['Actions per scenario']
assert abs(float(a['difference']))<1e-15
assert int(a['bounded_better_n'])==0
assert int(a['tie_n'])==760
assert int(a['comparator_better_n'])==0
assert abs(float(a['leave_one_family_out_min']))<1e-15
assert abs(float(a['leave_one_family_out_max']))<1e-15

print('Issue 11 strong deterministic-comparator tests: PASS')
