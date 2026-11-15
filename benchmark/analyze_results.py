"""Descriptive paired analysis for the finite constructed benchmark.

The 760 scenarios are the complete frozen benchmark suite, not an iid sample
from a population of possible biomedical-agent tasks.  Therefore this module
intentionally does NOT calculate population-level hypothesis-test P values or
interpret bootstrap intervals as confidence intervals for external deployment.

Instead it reports exact finite-benchmark paired effects plus family-structured
sensitivity summaries that show whether an effect is concentrated in one
scenario family.
"""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results" / "generated"


def _paired_summary(diff, family, *, higher_is_better=True):
    """Summarize one exact paired finite-benchmark difference vector.

    `diff` is always bounded - comparator.  `higher_is_better` controls only
    the win/loss labels; the reported numerical difference retains that sign.
    """
    diff = np.asarray(diff, dtype=float)
    family = np.asarray(family, dtype=str)
    if len(diff) != len(family):
        raise ValueError("diff/family length mismatch")

    eps = 1e-12
    tie = np.isclose(diff, 0.0, rtol=0.0, atol=eps)
    if higher_is_better:
        better = diff > eps
        worse = diff < -eps
    else:
        better = diff < -eps
        worse = diff > eps

    famdf = pd.DataFrame({"family": family, "difference": diff})
    family_effects = famdf.groupby("family", sort=True).difference.mean()

    # Deterministic leave-one-family-out sensitivity: recompute the exact
    # benchmark mean after omitting each entire scenario family once.
    loo = []
    for fam in family_effects.index:
        keep = family != fam
        loo.append(float(diff[keep].mean()))

    return {
        "difference": float(diff.mean()),
        "median_paired_difference": float(np.median(diff)),
        "bounded_better_n": int(better.sum()),
        "tie_n": int(tie.sum()),
        "comparator_better_n": int(worse.sum()),
        "family_median_difference": float(family_effects.median()),
        "family_min_difference": float(family_effects.min()),
        "family_max_difference": float(family_effects.max()),
        "leave_one_family_out_min": float(min(loo)),
        "leave_one_family_out_max": float(max(loo)),
        "n_scenarios": int(len(diff)),
        "n_families": int(len(family_effects)),
        "inference_scope": "finite constructed benchmark; descriptive, not population inference",
    }, family_effects


# ---------------------------------------------------------------------------
# Four-controller benchmark: exact bounded-minus-comparator policy effects.
# ---------------------------------------------------------------------------
bench = pd.read_csv(RES / "benchmark_trajectory_level.csv")
bounded = bench[bench.system.eq("Bounded controller")].sort_values("scenario_id")
comparators = ["Static workflow", "Goal planner", "Adaptive planner"]
rows = []
family_rows = []
for comp in comparators:
    g = bench[bench.system.eq(comp)].sort_values("scenario_id")
    if not np.array_equal(bounded.scenario_id.to_numpy(), g.scenario_id.to_numpy()):
        raise ValueError(f"Scenario alignment mismatch for {comp}")
    diff = bounded.policy_conformance.to_numpy(float) - g.policy_conformance.to_numpy(float)
    summary, fam = _paired_summary(diff, bounded.family.to_numpy(), higher_is_better=True)
    summary = {"comparison": f"vs {comp.replace(' workflow','')}", **summary}
    rows.append(summary)
    for family, effect in fam.items():
        family_rows.append({"comparison": summary["comparison"], "family": family, "difference": float(effect)})

primary = pd.DataFrame(rows)
primary.to_csv(RES / "primary_paired_policy_comparisons.csv", index=False)
pd.DataFrame(family_rows).to_csv(RES / "primary_policy_comparisons_by_family.csv", index=False)

# ---------------------------------------------------------------------------
# Bounded versus strong deterministic comparator.
# ---------------------------------------------------------------------------
det = pd.read_csv(RES / "deterministic_error_handling_trajectory_level.csv").sort_values("scenario_id")
if not np.array_equal(bounded.scenario_id.to_numpy(), det.scenario_id.to_numpy()):
    raise ValueError("Scenario alignment mismatch for deterministic comparator")

comparisons = []
det_family_rows = []
metric_specs = [
    ("Action appropriateness", bounded.action_appropriateness.to_numpy(float), det.action_appropriateness.to_numpy(float), True),
    ("Resource stewardship", bounded.resource_stewardship.to_numpy(float), det.resource_stewardship.to_numpy(float), True),
    ("Actions per scenario", bounded.actions_n.to_numpy(float), det.actions_n.to_numpy(float), False),
    ("Normalized workflow cost", bounded.actual_cost.to_numpy(float), det.actual_cost.to_numpy(float), False),
]
for metric, bvals, dvals, higher_is_better in metric_specs:
    diff = bvals - dvals
    summary, fam = _paired_summary(diff, bounded.family.to_numpy(), higher_is_better=higher_is_better)
    row = {
        "metric": metric,
        "bounded_mean": float(np.mean(bvals)),
        "deterministic_mean": float(np.mean(dvals)),
        **summary,
    }
    comparisons.append(row)
    for family, effect in fam.items():
        det_family_rows.append({"metric": metric, "family": family, "difference": float(effect)})

pd.DataFrame(comparisons).to_csv(RES / "bounded_vs_deterministic_paired_comparison.csv", index=False)
pd.DataFrame(det_family_rows).to_csv(RES / "bounded_vs_deterministic_by_family.csv", index=False)

print("\nPrimary policy comparisons — finite benchmark descriptive effects")
print(primary.to_string(index=False))
print("\nBounded vs deterministic — finite benchmark descriptive effects")
print(pd.DataFrame(comparisons).to_string(index=False))
