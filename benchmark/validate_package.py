#!/usr/bin/env python3
from pathlib import Path
import hashlib,json
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'/'frozen'
def sha256(p):
    h=hashlib.sha256(); h.update(Path(p).read_bytes()); return h.hexdigest()
def main():
    ctrl=pd.read_csv(DATA/'controller_input_manifest.csv').fillna(''); ref=pd.read_csv(DATA/'reference_policy.csv').fillna(''); fam=pd.read_csv(DATA/'scenario_family_definitions.csv').fillna(''); reg=pd.read_csv(DATA/'action_registry.csv').fillna('')
    assert len(ctrl)==760==len(ref); assert ctrl.scenario_id.is_unique and ref.scenario_id.is_unique; assert set(ctrl.scenario_id)==set(ref.scenario_id)
    forbidden={'family','reference_outcome','required_artifacts','require_escalation','require_human_review','require_provenance','require_verification','require_safe_block','forbidden_actions'}
    assert forbidden.isdisjoint(ctrl.columns), forbidden & set(ctrl.columns); assert 'family' in ref.columns
    merged=ctrl.merge(ref,on=['scenario_id','scenario_key'],validate='one_to_one'); assert merged.reference_outcome.value_counts().to_dict()=={'COMPLETE':629,'FAIL_SAFE':71,'BLOCK':60}
    assert ref.family.value_counts().to_dict()==dict(zip(fam.family,fam.n))
    expected_cols={'action_id','normalized_cost','prerequisites','produces','category','prohibited_in_clinical_request'}; assert set(reg.columns)==expected_cols; assert reg.action_id.is_unique
    produced=set(reg.produces)
    for _,row in reg.iterrows():
        req={x for x in str(row.prerequisites).split('|') if x}; assert req.issubset(produced); assert int(row.prohibited_in_clinical_request) in {0,1}
    goals=json.loads((DATA/'goal_definitions.json').read_text()); regmap=reg.set_index('action_id').to_dict('index')
    for g,spec in goals.items():
        artifacts=set()
        for a in spec['sequence']:
            assert a in regmap; req={x for x in str(regmap[a]['prerequisites']).split('|') if x}; assert req.issubset(artifacts),(g,a,req-artifacts); artifacts.add(regmap[a]['produces'])
        assert set(spec['required_artifacts']).issubset(artifacts)
    freeze=json.loads((DATA/'FREEZE_MANIFEST.json').read_text())
    for n,d in freeze['files'].items(): assert sha256(DATA/n)==d,n
    print('Comparator package integrity checks: PASS')
if __name__=='__main__': main()
