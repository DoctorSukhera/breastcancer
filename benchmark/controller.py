from dataclasses import dataclass, field
from pathlib import Path
import csv, json

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'/'frozen'
with open(DATA/'goal_definitions.json') as f:
    GOALS=json.load(f)
ACTION_REGISTRY={}; ACTION_COST={}; ACTION_CATEGORY={}; ACTION_PROHIBITED={}
with open(DATA/'action_registry.csv') as f:
    for r in csv.DictReader(f):
        spec={
            'normalized_cost':float(r['normalized_cost']),
            'prerequisites':{x for x in str(r.get('prerequisites','')).split('|') if x},
            'produces':r['produces'],
            'category':r['category'],
            'prohibited_in_clinical_request':bool(int(r.get('prohibited_in_clinical_request',0))),
        }
        ACTION_REGISTRY[r['action_id']]=spec
        ACTION_COST[r['action_id']]=spec['normalized_cost']
        ACTION_CATEGORY[r['action_id']]=spec['category']
        ACTION_PROHIBITED[r['action_id']]=spec['prohibited_in_clinical_request']

@dataclass
class RunState:
    system:str
    action_trace:list[str]=field(default_factory=list)
    artifacts:set[str]=field(default_factory=set)
    actual_outcome:str='ERROR'
    verification_performed:bool=False
    provenance_ok:bool=False
    escalated:bool=False
    safe_block:bool=False
    failed_attempts:int=0
    prerequisite_violations:int=0
    prohibited_attempts:int=0
    stopping_reason:str=''
    @property
    def actual_cost(self):
        return sum(ACTION_COST[a] for a in self.action_trace if a in ACTION_COST)
    @property
    def actions_n(self):
        return len(self.action_trace)

def _split_pipe(value):
    if value is None: return set()
    text=str(value).strip()
    if not text or text.lower()=='nan': return set()
    return {x for x in text.split('|') if x}

def _prohibited_request(s): return bool(str(s.get('prohibited_pattern','')).strip())
def _verification_signal_present(s): return float(s.get('mapping_loss',0.0))>0.0
def _evidence_inadequate(s): return float(s.get('mapping_loss',0.0))>0.25
def _primary_unavailable(s): return 'expression_gdc' in _split_pipe(s.get('unavailable_actions',''))
def _fallback_available(s): return bool(int(s.get('fallback_available',0)))
def _irrecoverable_source_loss(s): return _primary_unavailable(s) and not _fallback_available(s)
def _transient_action(s): return str(s.get('transient_fail_action','')).strip()
def _has_transient_failure(s): return bool(_transient_action(s))
def _provenance_corrupted(s): return bool(int(s.get('provenance_corrupted',0)))
def _prefer_low_cost(s): return bool(int(s.get('resource_prefer_low_cost',0)))

def _produced(action):
    spec=ACTION_REGISTRY.get(action); return None if spec is None else spec['produces']

def _apply_action(state,action,successful=True,scenario=None,enforce_prohibition=False):
    if action not in ACTION_REGISTRY:
        return False,'unregistered'
    state.action_trace.append(action)
    spec=ACTION_REGISTRY[action]
    if scenario is not None and _prohibited_request(scenario) and spec['prohibited_in_clinical_request']:
        state.prohibited_attempts += 1
        if enforce_prohibition:
            return False,'prohibited'
    missing=spec['prerequisites']-state.artifacts
    if successful and missing:
        state.prerequisite_violations += 1
        return False,'missing_prerequisite'
    if successful:
        art=spec['produces']
        if art: state.artifacts.add(art)
    return bool(successful),('ok' if successful else 'execution_failure')

def _goal_sequence(s):
    return list(GOALS[str(s['goal_name'])]['sequence'])

def _correct_scientific_route(s,include_audit=False):
    if _prohibited_request(s):
        return []
    if _evidence_inadequate(s) or _irrecoverable_source_loss(s):
        return ['human_review_gate','provenance_log']
    seq=_goal_sequence(s)
    if (_primary_unavailable(s) and _fallback_available(s)) or _prefer_low_cost(s):
        seq=['expression_cache' if a=='expression_gdc' else a for a in seq]

    # Transient semantics are explicit and mode-specific.
    transient=_transient_action(s)
    if transient and transient in seq:
        pos=seq.index(transient)
        mode=str(s.get('transient_mode','')).strip()
        if mode=='retry':
            # First attempt is injected to fail at runtime; second occurrence is
            # the successful retry of the same registered action.
            seq.insert(pos+1,transient)
        elif mode=='fallback':
            if transient=='expression_gdc' and _fallback_available(s):
                seq.insert(pos+1,'expression_cache')
            else:
                raise ValueError('Fallback-mode transient has no registered fallback')
        else:
            raise ValueError(f'Unsupported transient_mode {mode!r}')

    if _provenance_corrupted(s):
        insert_at=seq.index('final_report') if 'final_report' in seq else len(seq)
        seq.insert(insert_at,'provenance_repair')
    if include_audit:
        insert_at=seq.index('final_report') if 'final_report' in seq else len(seq)
        seq.insert(insert_at,'audit_log')
    return seq

def _finalize_from_observables(state,s):
    if _prohibited_request(s):
        state.actual_outcome='BLOCK'; state.safe_block=True; state.stopping_reason='safety_pre_gate'; return
    if _verification_signal_present(s):
        state.verification_performed=True
        if _evidence_inadequate(s):
            state.actual_outcome='FAIL_SAFE'; state.escalated=True; state.provenance_ok=True; state.stopping_reason='evidence_quality_fail_safe'; return
    if _irrecoverable_source_loss(s):
        state.actual_outcome='FAIL_SAFE'; state.escalated=True; state.provenance_ok=True; state.stopping_reason='irrecoverable_source_loss'; return
    state.actual_outcome='COMPLETE'; state.provenance_ok=True; state.stopping_reason='goal_complete'

class BoundedController:
    name='Bounded controller'
    def run(self,s):
        state=RunState(self.name)
        route=_correct_scientific_route(s)
        transient=_transient_action(s)
        for a in route:
            if transient and a==transient and state.failed_attempts==0:
                _apply_action(state,a,successful=False,scenario=s,enforce_prohibition=True)
                state.failed_attempts += 1
                continue
            ok,why=_apply_action(state,a,scenario=s,enforce_prohibition=True)
            if not ok:
                state.actual_outcome='ERROR'; state.stopping_reason=f'execution_{why}'; return state
        _finalize_from_observables(state,s)
        return state

class DeterministicErrorHandlingWorkflow:
    """Strong conventional deterministic error-handling comparator.

    This comparator is deliberately *goal-specific* rather than a forced
    full-workflow baseline.  It implements a transparent conventional policy:

      1. hard-block prohibited clinical requests;
      2. use the same fixed evidence threshold / irrecoverable-loss fail-safe;
      3. execute the requested canonical or held-out goal sequence;
      4. substitute the registered cache only for a known pre-execution primary
         source outage;
      5. on a runtime transient failure, retry the same action once (retry-first
         deterministic recovery), irrespective of the bounded controller's
         scenario-specific retry-vs-fallback choice;
      6. repair corrupted provenance before reporting;
      7. do not perform cost-aware source optimization.

    There is no full_prioritization override, no unconditional audit action,
    and no deliberately redundant execution.  Any performance difference from
    the bounded controller therefore emerges from recovery/optimization policy,
    not from forcing this comparator to run irrelevant analyses.
    """

    name='Deterministic error-handling workflow'

    def _plan(self, s):
        seq=list(_goal_sequence(s))

        # Conventional preflight handling: if the primary source is already
        # known to be unavailable, use the registered fallback.  Resource-stress
        # preference alone does not trigger optimization in this comparator.
        if _primary_unavailable(s):
            if not _fallback_available(s):
                return None
            seq=['expression_cache' if a=='expression_gdc' else a for a in seq]

        # Deterministic provenance repair is mandatory when corruption is
        # observable.  No optional audit step is injected.
        if _provenance_corrupted(s):
            insert_at=seq.index('final_report') if 'final_report' in seq else len(seq)
            seq.insert(insert_at,'provenance_repair')
        return seq

    def run(self,s):
        state=RunState(self.name)

        if _prohibited_request(s):
            state.actual_outcome='BLOCK'
            state.safe_block=True
            state.stopping_reason='safety_pre_gate'
            return state

        if _evidence_inadequate(s) or _irrecoverable_source_loss(s):
            for a in ['human_review_gate','provenance_log']:
                ok,why=_apply_action(state,a,scenario=s,enforce_prohibition=True)
                if not ok:
                    state.actual_outcome='ERROR'
                    state.stopping_reason=f'execution_{why}'
                    return state
            state.actual_outcome='FAIL_SAFE'
            state.escalated=True
            state.provenance_ok=True
            state.verification_performed=_verification_signal_present(s)
            state.stopping_reason='evidence_quality_fail_safe' if _evidence_inadequate(s) else 'irrecoverable_source_loss'
            return state

        route=self._plan(s)
        if route is None:
            state.actual_outcome='ERROR'
            state.stopping_reason='preflight_no_valid_expression_route'
            return state

        transient=_transient_action(s)
        transient_failed=False
        for a in route:
            # Conventional retry-first policy: the injected transient affects
            # the first attempt only; retry the *same* action once.  This is
            # intentionally independent of scenario transient_mode.
            if transient and a==transient and not transient_failed:
                _apply_action(state,a,successful=False,scenario=s,enforce_prohibition=True)
                state.failed_attempts += 1
                transient_failed=True
                ok,why=_apply_action(state,a,scenario=s,enforce_prohibition=True)
                if not ok:
                    state.actual_outcome='ERROR'
                    state.stopping_reason=f'retry_{why}_failure'
                    return state
                continue

            ok,why=_apply_action(state,a,scenario=s,enforce_prohibition=True)
            if not ok:
                state.actual_outcome='ERROR'
                state.stopping_reason=f'execution_{why}'
                return state

        state.actual_outcome='COMPLETE'
        state.provenance_ok=True
        state.verification_performed=_verification_signal_present(s)
        state.stopping_reason='deterministic_goal_workflow_complete'
        return state

class _BaselineExecutionMixin:
    def _attempt(self,state,s,action,transient_seen):
        unavailable=_split_pipe(s.get('unavailable_actions',''))
        if action in unavailable:
            _apply_action(state,action,successful=False,scenario=s,enforce_prohibition=False); state.failed_attempts += 1; return False,'unavailable'
        transient=_transient_action(s)
        if transient and action==transient and action not in transient_seen:
            transient_seen.add(action); _apply_action(state,action,successful=False,scenario=s,enforce_prohibition=False); state.failed_attempts += 1; return False,'transient'
        return _apply_action(state,action,successful=True,scenario=s,enforce_prohibition=False)
    def _finish_success(self,state,s,reason):
        state.actual_outcome='COMPLETE'; state.provenance_ok=('provenance_log' in state.action_trace and not _provenance_corrupted(s)); state.verification_performed=False; state.escalated=False; state.safe_block=False; state.stopping_reason=reason; return state
    def _finish_failure(self,state,reason):
        state.actual_outcome='ERROR'; state.provenance_ok=False; state.verification_performed=False; state.escalated=False; state.safe_block=False; state.stopping_reason=reason; return state

class StaticWorkflow(_BaselineExecutionMixin):
    name='Static workflow'
    def run(self,s):
        state=RunState(self.name); seen=set(); route=['static_dispatch']+list(GOALS['full_prioritization']['sequence'])
        for a in route:
            ok,why=self._attempt(state,s,a,seen)
            if not ok: return self._finish_failure(state,f'fixed_workflow_{why}_failure')
        return self._finish_success(state,s,'fixed_workflow_complete')

class GoalPlanner(_BaselineExecutionMixin):
    name='Goal planner'
    def _plan(self,s):
        seq=list(_goal_sequence(s))
        if _primary_unavailable(s) and _fallback_available(s):
            seq=['expression_cache' if a=='expression_gdc' else a for a in seq]
        return ['goal_planning_overhead']+seq
    def run(self,s):
        state=RunState(self.name); seen=set()
        for a in self._plan(s):
            ok,why=self._attempt(state,s,a,seen)
            if not ok: return self._finish_failure(state,f'planned_route_{why}_failure')
        return self._finish_success(state,s,'goal_plan_complete')

class AdaptivePlanner(_BaselineExecutionMixin):
    name='Adaptive planner'
    def _initial_plan(self,s):
        seq=list(_goal_sequence(s))
        if _primary_unavailable(s) and _fallback_available(s):
            seq=['expression_cache' if a=='expression_gdc' else a for a in seq]
        return seq
    def run(self,s):
        state=RunState(self.name); seen=set(); route=self._initial_plan(s); i=0
        while i<len(route):
            a=route[i]; ok,why=self._attempt(state,s,a,seen)
            if ok: i+=1; continue
            if why=='transient':
                mode=str(s.get('transient_mode','')).strip()
                if mode=='retry':
                    ok2,why2=self._attempt(state,s,a,seen)
                    if not ok2: return self._finish_failure(state,f'retry_{why2}_failure')
                    i+=1; continue
                if mode=='fallback' and a=='expression_gdc' and _fallback_available(s):
                    ok2,why2=self._attempt(state,s,'expression_cache',seen)
                    if not ok2: return self._finish_failure(state,f'fallback_{why2}_failure')
                    i+=1; continue
            return self._finish_failure(state,f'adaptive_{why}_failure')
        return self._finish_success(state,s,'adaptive_plan_complete')

def controller_suite():
    return [StaticWorkflow(),GoalPlanner(),AdaptivePlanner(),BoundedController()]
