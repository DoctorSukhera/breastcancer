from pathlib import Path
import csv,json
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'/'frozen'
with open(DATA/'goal_definitions.json') as f: GOALS=json.load(f)
ACTION_COST={}
with open(DATA/'action_registry.csv') as f:
    for r in csv.DictReader(f): ACTION_COST[r['action_id']]=float(r['normalized_cost'])

def _split_pipe(v):
    if v is None: return set()
    t=str(v).strip()
    if not t or t.lower()=='nan': return set()
    return {x for x in t.split('|') if x}

def oracle_trace(s,ref):
    outcome=str(ref['reference_outcome'])
    if outcome=='BLOCK': return []
    if outcome=='FAIL_SAFE': return ['human_review_gate','provenance_log']
    if outcome!='COMPLETE': raise ValueError(outcome)
    seq=list(GOALS[str(s['goal_name'])]['sequence'])
    unavailable=_split_pipe(s.get('unavailable_actions','')); fallback=bool(int(s.get('fallback_available',0))); prefer=bool(int(s.get('resource_prefer_low_cost',0)))
    if 'expression_gdc' in seq:
        if 'expression_gdc' in unavailable:
            if not fallback: raise ValueError('COMPLETE reference without available expression route')
            seq[seq.index('expression_gdc')]='expression_cache'
        elif prefer and fallback and ACTION_COST['expression_cache']<ACTION_COST['expression_gdc']:
            seq[seq.index('expression_gdc')]='expression_cache'
    transient=str(s.get('transient_fail_action','')).strip(); mode=str(s.get('transient_mode','')).strip()
    if transient:
        if transient!='expression_gdc': raise ValueError(f'No recovery rule for {transient}')
        if mode=='retry':
            if 'expression_gdc' not in seq: raise ValueError('Retry requires primary in route')
            pos=seq.index('expression_gdc'); seq.insert(pos,'expression_gdc')
        elif mode=='fallback':
            if not fallback: raise ValueError('Fallback unavailable')
            if 'expression_gdc' in seq: pos=seq.index('expression_gdc'); seq[pos]='expression_cache'
            elif 'expression_cache' in seq: pos=seq.index('expression_cache')
            else: raise ValueError('No expression route')
            seq.insert(pos,'expression_gdc')
        else: raise ValueError(f'Unsupported transient_mode {mode!r}')
    if bool(int(s.get('provenance_corrupted',0))):
        if 'provenance_log' not in seq: raise ValueError('Repair requires provenance log')
        pos=seq.index('final_report') if 'final_report' in seq else len(seq); seq.insert(pos,'provenance_repair')
    return seq

def oracle_cost(s,ref): return float(sum(ACTION_COST[a] for a in oracle_trace(s,ref)))

def resource_stewardship(actual_cost,s,ref,actual_outcome=None):
    outcome=str(ref['reference_outcome']); actual=float(actual_cost)
    if outcome=='BLOCK':
        return 1.0 if actual_outcome=='BLOCK' and actual==0.0 else 0.0
    if actual<=0: return 0.0
    return min(1.0,oracle_cost(s,ref)/actual)
