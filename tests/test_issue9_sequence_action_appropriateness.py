from pathlib import Path
import sys
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'/'frozen'
sys.path.insert(0,str(ROOT/'benchmark'))
from controller import RunState
from evaluator import assess_action_appropriateness
from oracle import oracle_trace

inputs=pd.read_csv(DATA/'controller_input_manifest.csv').fillna('')
refs=pd.read_csv(DATA/'reference_policy.csv').fillna('')
refmap={int(r.scenario_id):r.to_dict() for _,r in refs.iterrows()}

def runtime(sid):
    s=inputs[inputs.scenario_id.eq(sid)].iloc[0].to_dict(); s['scenario_id']=int(sid)
    return s,refmap[int(sid)]

def state(trace, prereq=0):
    st=RunState('unit-test'); st.action_trace=list(trace); st.prerequisite_violations=prereq
    return st

# Clean COMPLETE case for controlled perturbations.
clean_sid=int(refs.loc[refs.family.eq('clean'),'scenario_id'].iloc[0])
s,ref=runtime(clean_sid); expected=oracle_trace(s,ref)
assert expected

# Exact reference and non-empty proper prefixes are appropriate.
assert assess_action_appropriateness(s,ref,state(expected))['appropriate']==1
assert assess_action_appropriateness(s,ref,state(expected[:2]))['appropriate']==1

# Doing nothing on a non-BLOCK task is not vacuously appropriate.
assert assess_action_appropriateness(s,ref,state([]))['appropriate']==0

# Wrong order fails even though all actions individually belong to the goal.
wrong=list(expected); wrong[0],wrong[1]=wrong[1],wrong[0]
assert set(wrong)==set(expected)
assert assess_action_appropriateness(s,ref,state(wrong))['appropriate']==0

# Unjustified duplicate fails even though the duplicated action is permitted.
dup=[expected[0],expected[0]]+expected[1:]
assert assess_action_appropriateness(s,ref,state(dup))['appropriate']==0

# Extra/unnecessary action after the prescribed trace fails.
extra=list(expected)+['audit_log']
assert assess_action_appropriateness(s,ref,state(extra))['appropriate']==0

# Registry/prerequisite-order violations are automatic failures.
assert assess_action_appropriateness(s,ref,state(expected,prereq=1))['appropriate']==0

# Unregistered action is an automatic failure.
assert assess_action_appropriateness(s,ref,state(['not_registered']))['appropriate']==0

# BLOCK requires no scientific/governance action attempt.
block_sid=int(refs.loc[refs.reference_outcome.eq('BLOCK'),'scenario_id'].iloc[0])
bs,br=runtime(block_sid)
assert oracle_trace(bs,br)==[]
assert assess_action_appropriateness(bs,br,state([]))['appropriate']==1
assert assess_action_appropriateness(bs,br,state(['expression_gdc']))['appropriate']==0

# Resource-stress route is sequence-specific: higher-cost primary is not an
# appropriate substitute for the prescribed cache route.
rs_sid=int(refs.loc[refs.family.eq('resource_stress'),'scenario_id'].iloc[0])
rs,rr=runtime(rs_sid); rtr=oracle_trace(rs,rr)
assert rtr[0]=='expression_cache'
assert assess_action_appropriateness(rs,rr,state(['expression_gdc']))['appropriate']==0

# Provenance attack: reporting without the required repair is a sequence error.
pa_sid=int(refs.loc[refs.family.eq('provenance_attack'),'scenario_id'].iloc[0])
ps,pr=runtime(pa_sid); ptr=oracle_trace(ps,pr)
assert 'provenance_repair' in ptr
no_repair=[a for a in ptr if a!='provenance_repair']
assert assess_action_appropriateness(ps,pr,state(no_repair))['appropriate']==0

print('Issue 9 sequence-aware action-appropriateness tests: PASS')
