from pathlib import Path
import pandas as pd
from controller import BoundedController, DeterministicErrorHandlingWorkflow
from evaluator import evaluate_run
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'/'frozen'; RES=ROOT/'results'/'generated'; RES.mkdir(parents=True,exist_ok=True)
inputs=pd.read_csv(DATA/'controller_input_manifest.csv').fillna(''); refs=pd.read_csv(DATA/'reference_policy.csv').fillna(''); refmap={int(r.scenario_id):r.to_dict() for _,r in refs.iterrows()}
bounded=BoundedController(); det=DeterministicErrorHandlingWorkflow(); rows=[]
for _,r in inputs.iterrows():
    s=r.to_dict(); s['scenario_id']=int(s['scenario_id']); ref=refmap[s['scenario_id']]
    b=bounded.run(s); d=det.run(s); ev=evaluate_run(s,ref,d)
    ev['bounded_actions_n']=b.actions_n; ev['bounded_cost']=b.actual_cost; rows.append(ev)
out=pd.DataFrame(rows); out.to_csv(RES/'deterministic_error_handling_trajectory_level.csv',index=False)
comp=out.reference_outcome.eq('COMPLETE')
summary=pd.DataFrame([{'system':'Deterministic error-handling workflow','n':len(out),'policy_conformance':out.policy_conformance.mean(),'feasible_goal_completion':out.loc[comp,'feasible_goal_completion'].dropna().mean(),'action_appropriateness':out.action_appropriateness.mean(),'safety_conformance':out.safety_conformance.mean(),'provenance_conformance':out.provenance_conformance.mean(),'escalation_conformance':out.escalation_conformance.mean(),'resource_stewardship':out.resource_stewardship.mean(),'mean_oracle_cost':out.oracle_cost.mean(),'mean_cost':out.actual_cost.mean(),'mean_actions':out.actions_n.mean(),'bounded_mean_cost':out.bounded_cost.mean(),'bounded_mean_actions':out.bounded_actions_n.mean()}])
summary.to_csv(RES/'deterministic_error_handling_summary.csv',index=False); print(summary.to_string(index=False))
