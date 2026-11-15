"""True module-disabled bounded-controller variants for architectural ablation.

Each variant executes every scenario from a fresh RunState.  No trajectory is
copied from the full bounded controller and no outcome/action trace is edited
after execution.  The switches below alter planning/execution behavior before
and during the run, so ablation effects emerge from actual controller behavior.
"""
from dataclasses import dataclass

from controller import (
    RunState, _apply_action, _goal_sequence,
    _prohibited_request, _verification_signal_present, _evidence_inadequate,
    _primary_unavailable, _fallback_available, _irrecoverable_source_loss,
    _transient_action, _provenance_corrupted, _prefer_low_cost,
)


@dataclass(frozen=True)
class AblationConfig:
    name: str
    replanning: bool = True
    verifier: bool = True
    safety_gate: bool = True
    provenance_repair: bool = True
    cost_awareness: bool = True


FULL = AblationConfig("Full bounded controller")
REPLANNING_OFF = AblationConfig("Replanning removed", replanning=False)
VERIFIER_OFF = AblationConfig("Verifier removed", verifier=False)
SAFETY_OFF = AblationConfig("Safety gate removed", safety_gate=False)
PROVENANCE_OFF = AblationConfig("Provenance removed", provenance_repair=False)
COST_OFF = AblationConfig("Cost-awareness removed", cost_awareness=False)


class AblatedBoundedController:
    """Bounded controller executed with one or more architectural modules off."""

    def __init__(self, config: AblationConfig):
        self.config = config
        self.name = config.name

    def _base_route(self, s):
        """Build the route before runtime transient-failure recovery."""
        cfg = self.config

        # Safety gate is an architectural pre-execution module.  If disabled,
        # the request proceeds through the ordinary scientific goal route.
        if cfg.safety_gate and _prohibited_request(s):
            return []

        # Evidence verifier is distinct from source-availability fail-safe.
        if cfg.verifier and _evidence_inadequate(s):
            return ["human_review_gate", "provenance_log"]
        if _irrecoverable_source_loss(s):
            return ["human_review_gate", "provenance_log"]

        seq = list(_goal_sequence(s))

        # Preflight source availability is retained in every variant: this is
        # ordinary plan feasibility, not runtime replanning.
        if _primary_unavailable(s) and _fallback_available(s):
            seq = ["expression_cache" if a == "expression_gdc" else a for a in seq]
        elif cfg.cost_awareness and _prefer_low_cost(s) and _fallback_available(s):
            # Cost-awareness module chooses the cheaper valid source.
            seq = ["expression_cache" if a == "expression_gdc" else a for a in seq]

        # Provenance enforcement inserts repair before final reporting.
        if cfg.provenance_repair and _provenance_corrupted(s):
            pos = seq.index("final_report") if "final_report" in seq else len(seq)
            seq.insert(pos, "provenance_repair")

        return seq

    def _fail(self, state, reason):
        state.actual_outcome = "ERROR"
        state.provenance_ok = False
        state.escalated = False
        state.safe_block = False
        state.stopping_reason = reason
        return state

    def _execute_action(self, state, s, action, *, successful=True):
        return _apply_action(
            state, action, successful=successful, scenario=s,
            enforce_prohibition=self.config.safety_gate,
        )

    def run(self, s):
        cfg = self.config
        state = RunState(self.name)

        # True pre-execution safety behavior.  With the gate removed, execution
        # continues from a fresh state rather than mutating a blocked trajectory.
        if cfg.safety_gate and _prohibited_request(s):
            state.actual_outcome = "BLOCK"
            state.safe_block = True
            state.stopping_reason = "safety_pre_gate"
            return state

        route = self._base_route(s)
        transient = _transient_action(s)
        transient_seen = False

        for action in route:
            # Inject the benchmark-defined first transient failure at runtime.
            if transient and action == transient and not transient_seen:
                transient_seen = True
                self._execute_action(state, s, action, successful=False)
                state.failed_attempts += 1
                mode = str(s.get("transient_mode", "")).strip()

                if mode == "retry":
                    # Local same-action retry remains available in the
                    # replanning-off ablation; it is not plan substitution.
                    ok, why = self._execute_action(state, s, action, successful=True)
                    if not ok:
                        return self._fail(state, f"retry_{why}_failure")
                    continue

                if mode == "fallback":
                    if cfg.replanning and action == "expression_gdc" and _fallback_available(s):
                        ok, why = self._execute_action(state, s, "expression_cache", successful=True)
                        if not ok:
                            return self._fail(state, f"fallback_{why}_failure")
                        continue
                    return self._fail(state, "runtime_replanning_disabled")

                return self._fail(state, f"unsupported_transient_mode_{mode}")

            ok, why = self._execute_action(state, s, action, successful=True)
            if not ok:
                return self._fail(state, f"execution_{why}")

        # Terminal interpretation is produced by the architecture actually run.
        if cfg.verifier and _verification_signal_present(s):
            state.verification_performed = True
            if _evidence_inadequate(s):
                state.actual_outcome = "FAIL_SAFE"
                state.escalated = True
                state.provenance_ok = True
                state.stopping_reason = "evidence_quality_fail_safe"
                return state

        if _irrecoverable_source_loss(s):
            state.actual_outcome = "FAIL_SAFE"
            state.escalated = True
            state.provenance_ok = True
            state.stopping_reason = "irrecoverable_source_loss"
            return state

        state.actual_outcome = "COMPLETE"
        state.safe_block = False
        # Without provenance enforcement, corrupted provenance remains invalid
        # even though the ordinary reporting route can technically complete.
        state.provenance_ok = not (_provenance_corrupted(s) and not cfg.provenance_repair)
        state.stopping_reason = "goal_complete"
        return state


def ablation_suite():
    return [
        AblatedBoundedController(FULL),
        AblatedBoundedController(REPLANNING_OFF),
        AblatedBoundedController(VERIFIER_OFF),
        AblatedBoundedController(SAFETY_OFF),
        AblatedBoundedController(PROVENANCE_OFF),
        AblatedBoundedController(COST_OFF),
    ]
