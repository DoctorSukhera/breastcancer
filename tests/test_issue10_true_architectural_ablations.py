from pathlib import Path
import inspect, sys
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'/'frozen'
sys.path.insert(0,str(ROOT/'benchmark'))

import ablation_controller as ac
from ablation_controller import (
    AblatedBoundedController, FULL, REPLANNING_OFF, VERIFIER_OFF,
    SAFETY_OFF, PROVENANCE_OFF, COST_OFF,
)
from controller import BoundedController

inputs=pd.read_csv(DATA/'controller_input_manifest.csv').fillna('')
refs=pd.read_csv(DATA/'reference_policy.csv').fillna('')
joined=inputs.merge(refs[['scenario_id','family','reference_outcome']],on='scenario_id',validate='one_to_one')


def state_signature(st):
    return (
        tuple(st.action_trace), tuple(sorted(st.artifacts)), st.actual_outcome,
        st.verification_performed, st.provenance_ok, st.escalated,
        st.safe_block, st.failed_attempts, st.prerequisite_violations,
        st.prohibited_attempts, st.stopping_reason,
    )


def runtime_for(family, **conditions):
    g=joined[joined.family.eq(family)]
    for key,val in conditions.items():
        g=g[g[key].astype(str).eq(str(val))]
    assert len(g),(family,conditions)
    sid=int(g.iloc[0].scenario_id)
    s=inputs[inputs.scenario_id.eq(sid)].iloc[0].to_dict(); s['scenario_id']=sid
    return s

# 1) Active runner/variant source must be true execution, not copied-state surgery.
runner=(ROOT/'benchmark'/'run_ablation.py').read_text()
assert 'import copy' not in runner
assert 'deepcopy' not in runner
assert 'copy.deepcopy' not in runner
assert 'st.action_trace=[' not in runner
assert "st.actual_outcome='" not in runner

# 2) Full configurable architecture must be behaviorally identical to the ordinary bounded controller.
full=AblatedBoundedController(FULL); bounded=BoundedController()
for _,row in inputs.iterrows():
    s=row.to_dict(); s['scenario_id']=int(s['scenario_id'])
    assert state_signature(full.run(s))==state_signature(bounded.run(s)),s['scenario_id']

# 3) Replanning-off: local retry remains, runtime fallback replanning does not.
rtry=runtime_for('transient_failure',transient_mode='retry')
rfb=runtime_for('transient_failure',transient_mode='fallback')
rep=AblatedBoundedController(REPLANNING_OFF)
assert rep.run(rtry).actual_outcome=='COMPLETE'
st=rep.run(rfb)
assert st.actual_outcome=='ERROR'
assert st.action_trace==['expression_gdc']
assert st.stopping_reason=='runtime_replanning_disabled'

# 4) Verifier-off: high-loss evidence proceeds through the ordinary goal route rather than inheriting fail-safe actions.
sev=runtime_for('evidence_quality',mapping_loss='0.3')
ver=AblatedBoundedController(VERIFIER_OFF).run(sev)
assert ver.actual_outcome=='COMPLETE'
assert not ver.verification_performed and not ver.escalated
assert 'human_review_gate' not in ver.action_trace
assert 'age_association' in ver.action_trace

# 5) Safety-off: prohibited requests actually execute from a fresh state and are not blocked.
proh=runtime_for('prohibited_clinical_request')
saf=AblatedBoundedController(SAFETY_OFF).run(proh)
assert saf.actual_outcome=='COMPLETE'
assert not saf.safe_block
assert saf.prohibited_attempts>0
assert len(saf.action_trace)>0

# 6) Provenance-off: corrupted provenance is not repaired and therefore remains nonconformant.
prov=runtime_for('provenance_attack')
pr=AblatedBoundedController(PROVENANCE_OFF).run(prov)
assert pr.actual_outcome=='COMPLETE'
assert 'provenance_repair' not in pr.action_trace
assert not pr.provenance_ok

# 7) Cost-awareness-off: use the valid primary route, with no artificial overuse action.
rs=runtime_for('resource_stress')
co=AblatedBoundedController(COST_OFF).run(rs)
fu=AblatedBoundedController(FULL).run(rs)
assert co.actual_outcome=='COMPLETE'
assert 'expression_gdc' in co.action_trace and 'expression_cache' not in co.action_trace
assert 'resource_overuse' not in co.action_trace
assert 'expression_cache' in fu.action_trace and 'expression_gdc' not in fu.action_trace
assert abs(co.actual_cost-fu.actual_cost-0.25)<1e-12
assert co.actions_n==fu.actions_n

print('Issue 10 true architectural-ablation tests: PASS')
