from pathlib import Path
import pandas as pd

from ablation_controller import ablation_suite
from evaluator import evaluate_run

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'/'frozen'
RES=ROOT/'results'/'generated'
RES.mkdir(parents=True,exist_ok=True)

inputs=pd.read_csv(DATA/'controller_input_manifest.csv').fillna('')
refs=pd.read_csv(DATA/'reference_policy.csv').fillna('')
refmap={int(r.scenario_id):r.to_dict() for _,r in refs.iterrows()}

rows=[]
for controller in ablation_suite():
    for _,rr in inputs.iterrows():
        s=rr.to_dict(); s['scenario_id']=int(s['scenario_id'])
        ref=refmap[s['scenario_id']]
        # Every variant starts from its own fresh RunState inside controller.run.
        state=controller.run(s)
        ev=evaluate_run(s,ref,state)
        ev['system']=controller.name
        rows.append(ev)

out=pd.DataFrame(rows)
out.to_csv(RES/'ablation_trajectory_level.csv',index=False)

summary=[]
for system,g in out.groupby('system',sort=False):
    transient=g.family.eq('transient_failure')
    prohibited=g.family.eq('prohibited_clinical_request')
    prov=g.family.eq('provenance_attack')
    evidence=g.family.eq('evidence_quality')
    irr=g.family.eq('irrecoverable_source_loss')
    summary.append({
        'system':system,
        'policy_conformance':g.policy_conformance.mean(),
        'action_appropriateness':g.action_appropriateness.mean(),
        'safety_conformance':g.safety_conformance.mean(),
        'provenance_conformance':g.provenance_conformance.mean(),
        'resource_stewardship':g.resource_stewardship.mean(),
        'mean_cost':g.actual_cost.mean(),
        'mean_actions':g.actions_n.mean(),
        'transient_recovery_rate':g.loc[transient,'actual_outcome'].eq('COMPLETE').mean(),
        'safe_block_rate':g.loc[prohibited,'actual_outcome'].eq('BLOCK').mean(),
        'provenance_attack_conformance':g.loc[prov,'policy_conformance'].mean(),
        'evidence_quality_conformance':g.loc[evidence,'policy_conformance'].mean(),
        'irrecoverable_loss_conformance':g.loc[irr,'policy_conformance'].mean(),
    })
sumdf=pd.DataFrame(summary)
sumdf.to_csv(RES/'ablation_summary_metrics.csv',index=False)
print(sumdf.to_string(index=False))
