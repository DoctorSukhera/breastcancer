from pathlib import Path
import pandas as pd
from controller import controller_suite
from evaluator import evaluate_run
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'/'frozen'; RES=ROOT/'results'/'generated'; RES.mkdir(parents=True,exist_ok=True)
inputs=pd.read_csv(DATA/'controller_input_manifest.csv').fillna(''); refs=pd.read_csv(DATA/'reference_policy.csv').fillna(''); refmap={int(r.scenario_id):r.to_dict() for _,r in refs.iterrows()}
rows=[]
for ctrl in controller_suite():
    for _,r in inputs.iterrows():
        s=r.to_dict(); s['scenario_id']=int(s['scenario_id']); rows.append(evaluate_run(s,refmap[s['scenario_id']],ctrl.run(s)))
out=pd.DataFrame(rows); out.to_csv(RES/'benchmark_trajectory_level.csv',index=False)
summ=[]
for system,g in out.groupby('system',sort=False):
    comp=g.reference_outcome.eq('COMPLETE')
    summ.append({'system':system,'n':len(g),'policy_conformance':g.policy_conformance.mean(),'feasible_goal_completion':g.loc[comp,'feasible_goal_completion'].dropna().mean(),'action_appropriateness':g.action_appropriateness.mean(),'safety_conformance':g.safety_conformance.mean(),'provenance_conformance':g.provenance_conformance.mean(),'escalation_conformance':g.escalation_conformance.mean(),'resource_stewardship':g.resource_stewardship.mean(),'mean_oracle_cost':g.oracle_cost.mean(),'mean_cost':g.actual_cost.mean(),'mean_actions':g.actions_n.mean()})
sumdf=pd.DataFrame(summ); sumdf.to_csv(RES/'benchmark_controller_summary.csv',index=False)
out[(out.system=='Bounded controller') & out.scenario_id.isin([34,286,439,522])].to_csv(RES/'representative_traces.csv',index=False)
print(sumdf.to_string(index=False))
