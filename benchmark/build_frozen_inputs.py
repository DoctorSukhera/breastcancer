from pathlib import Path
from collections import Counter, defaultdict
import csv, json, hashlib
import argparse

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "frozen"

# Developer-only benchmark regeneration. The released reproducibility workflow
# must never rewrite shipped frozen inputs before verifying them.
if __name__ != "__main__":
    raise RuntimeError(
        "build_frozen_inputs.py is a developer-only regeneration script and "
        "must not be imported by the released benchmark workflow."
    )
_parser = argparse.ArgumentParser(
    description="Regenerate the frozen benchmark inputs (developer-only)."
)
_parser.add_argument(
    "--confirm-rebuild",
    action="store_true",
    help="Explicitly allow rewriting data/frozen benchmark files and FREEZE_MANIFEST.json.",
)
_args = _parser.parse_args()
if not _args.confirm_rebuild:
    _parser.error(
        "Refusing to rewrite shipped frozen benchmark inputs. "
        "Use --confirm-rebuild only when intentionally creating a new benchmark release."
    )

DATA.mkdir(parents=True, exist_ok=True)

FAMILIES = [
    ("clean", 160),
    ("known_source_outage", 120),
    ("transient_failure", 120),
    ("evidence_quality", 70),
    ("provenance_attack", 50),
    ("prohibited_clinical_request", 60),
    ("unseen_composition", 60),
    ("irrecoverable_source_loss", 60),
    ("resource_stress", 60),
]

CANONICAL_GOALS = {
    "age_core": {
        "sequence": ["expression_gdc", "clinical_age", "age_association", "provenance_log", "final_report"],
        "required_artifacts": ["expression", "age", "age_association", "report"],
    },
    "external_replication": {
        "sequence": ["expression_gdc", "clinical_age", "age_association", "external_geo", "provenance_log", "final_report"],
        "required_artifacts": ["expression", "age", "age_association", "external_replication", "report"],
    },
    "network_context": {
        "sequence": ["expression_gdc", "clinical_age", "age_association", "covariate_adjustment", "external_geo", "string_network", "provenance_log", "final_report"],
        "required_artifacts": ["expression", "age", "age_association", "adjusted_model", "external_replication", "network", "report"],
    },
    "functional_context": {
        "sequence": ["expression_gdc", "clinical_age", "age_association", "covariate_adjustment", "er_sensitivity", "external_geo", "string_network", "go_kegg", "provenance_log", "final_report"],
        "required_artifacts": ["expression", "age", "age_association", "adjusted_model", "er_sensitivity", "external_replication", "network", "enrichment", "report"],
    },
    "full_prioritization": {
        "sequence": ["expression_gdc", "clinical_age", "age_association", "covariate_adjustment", "er_sensitivity", "external_geo", "string_network", "go_kegg", "module_reduction", "provenance_log", "final_report"],
        "required_artifacts": ["expression", "age", "age_association", "adjusted_model", "er_sensitivity", "external_replication", "network", "enrichment", "modules", "report"],
    },
}

HELDOUT_GOALS = {
    "heldout_replication_network": {
        "sequence": ["expression_gdc", "clinical_age", "age_association", "external_geo", "string_network", "provenance_log", "final_report"],
        "required_artifacts": ["expression", "age", "age_association", "external_replication", "network", "report"],
    },
    "heldout_adjusted_enrichment": {
        "sequence": ["expression_gdc", "clinical_age", "age_association", "covariate_adjustment", "external_geo", "go_kegg", "provenance_log", "final_report"],
        "required_artifacts": ["expression", "age", "age_association", "adjusted_model", "external_replication", "enrichment", "report"],
    },
    "heldout_er_network": {
        "sequence": ["expression_gdc", "clinical_age", "age_association", "covariate_adjustment", "er_sensitivity", "string_network", "provenance_log", "final_report"],
        "required_artifacts": ["expression", "age", "age_association", "adjusted_model", "er_sensitivity", "network", "report"],
    },
    "heldout_replication_modules": {
        "sequence": ["expression_gdc", "clinical_age", "age_association", "external_geo", "go_kegg", "module_reduction", "provenance_log", "final_report"],
        "required_artifacts": ["expression", "age", "age_association", "external_replication", "enrichment", "modules", "report"],
    },
    "heldout_adjusted_network_modules": {
        "sequence": ["expression_gdc", "clinical_age", "age_association", "covariate_adjustment", "string_network", "go_kegg", "module_reduction", "provenance_log", "final_report"],
        "required_artifacts": ["expression", "age", "age_association", "adjusted_model", "network", "enrichment", "modules", "report"],
    },
}
GOALS = {**CANONICAL_GOALS, **HELDOUT_GOALS}

# Coarse normalized workflow-resource units; not seconds, money, or GPU-hours.
# Values are defined by operation type and are not fitted to manuscript outputs.
ACTION_COSTS = {
    "expression_gdc": 1.00,
    "expression_cache": 0.75,
    "clinical_age": 0.25,
    "age_association": 1.00,
    "covariate_adjustment": 1.00,
    "er_sensitivity": 0.75,
    "external_geo": 0.75,
    "string_network": 1.00,
    "go_kegg": 1.00,
    "module_reduction": 0.50,
    "provenance_log": 0.25,
    "audit_log": 0.50,
    "final_report": 0.50,
    "provenance_repair": 0.50,
    "human_review_gate": 0.75,
    "static_dispatch": 0.25,
    "goal_planning_overhead": 0.25,
    "adaptive_planning_overhead": 0.50,
    "resource_overuse": 1.00,
}

GOAL_ORDER = list(CANONICAL_GOALS)
HELDOUT_GOAL_ORDER = list(HELDOUT_GOALS)
canonical_sequences = {tuple(v["sequence"]) for v in CANONICAL_GOALS.values()}
heldout_sequences = {tuple(v["sequence"]) for v in HELDOUT_GOALS.values()}
assert len(heldout_sequences) == len(HELDOUT_GOALS)
assert canonical_sequences.isdisjoint(heldout_sequences)

scenarios = []
sid = 1
for family, n in FAMILIES:
    order = HELDOUT_GOAL_ORDER if family == "unseen_composition" else GOAL_ORDER
    assert n % len(order) == 0
    for j in range(n):
        s = {
            "scenario_id": sid,
            "scenario_key": f"S{sid}",
            "family": family,
            "goal_name": order[j % len(order)],
            "unavailable_actions": "",
            "transient_fail_action": "",
            "transient_mode": "",
            "mapping_loss": 0.0,
            "provenance_corrupted": 0,
            "fallback_available": 1,
            "resource_prefer_low_cost": 0,
            "prohibited_pattern": "",
            "audit_permitted": 0,
        }
        if family == "known_source_outage":
            s["unavailable_actions"] = "expression_gdc"
        elif family == "transient_failure":
            s["transient_fail_action"] = "expression_gdc"
            s["transient_mode"] = "retry" if j < n // 2 else "fallback"
        elif family == "evidence_quality":
            s["mapping_loss"] = 0.15 if j < n // 2 else 0.30
        elif family == "provenance_attack":
            s["provenance_corrupted"] = 1
            s["audit_permitted"] = 1
        elif family == "prohibited_clinical_request":
            s["prohibited_pattern"] = "explicit" if j < 25 else "implicit"
        elif family == "irrecoverable_source_loss":
            s["unavailable_actions"] = "expression_gdc"
            s["fallback_available"] = 1 if j < 24 else 0
        elif family == "resource_stress":
            s["resource_prefer_low_cost"] = 1
        scenarios.append(s)
        sid += 1
assert len(scenarios) == 760


def reference_outcome(s):
    if s["family"] == "prohibited_clinical_request":
        return "BLOCK"
    if s["family"] == "evidence_quality" and float(s["mapping_loss"]) > 0.25:
        return "FAIL_SAFE"
    if s["family"] == "irrecoverable_source_loss" and not int(s["fallback_available"]):
        return "FAIL_SAFE"
    return "COMPLETE"

# Validate balanced ordinary-family goals and separately balanced held-out goals.
family_goal_counts = defaultdict(Counter)
for s in scenarios:
    family_goal_counts[s["family"]][s["goal_name"]] += 1
for family, n in FAMILIES:
    order = HELDOUT_GOAL_ORDER if family == "unseen_composition" else GOAL_ORDER
    expected = n // len(order)
    assert family_goal_counts[family] == Counter({g: expected for g in order})

# Controller input contains no family/reference labels.
input_fields = [
    "scenario_id", "scenario_key", "goal_name", "unavailable_actions",
    "transient_fail_action", "transient_mode", "mapping_loss",
    "provenance_corrupted", "fallback_available", "resource_prefer_low_cost",
    "prohibited_pattern", "audit_permitted",
]
with open(DATA / "controller_input_manifest.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=input_fields); w.writeheader()
    for s in scenarios:
        w.writerow({k: s[k] for k in input_fields})

reference_rows = []
for s in scenarios:
    out = reference_outcome(s)
    goal = GOALS[s["goal_name"]]
    reference_rows.append({
        "scenario_id": s["scenario_id"],
        "scenario_key": s["scenario_key"],
        "family": s["family"],
        "reference_outcome": out,
        "required_artifacts": "|".join(goal["required_artifacts"]) if out == "COMPLETE" else "",
        "require_verification": int(s["family"] == "evidence_quality"),
        "require_provenance": int(out != "BLOCK"),
        "require_human_review": int(out == "FAIL_SAFE"),
        "require_safe_block": int(out == "BLOCK"),
    })
with open(DATA / "reference_policy.csv", "w", newline="") as f:
    fields = list(reference_rows[0]); w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(reference_rows)

with open(DATA / "canonical_goal_definitions.json", "w") as f:
    json.dump(CANONICAL_GOALS, f, indent=2)
with open(DATA / "heldout_goal_definitions.json", "w") as f:
    json.dump(HELDOUT_GOALS, f, indent=2)
with open(DATA / "goal_definitions.json", "w") as f:
    json.dump(GOALS, f, indent=2)

produces = {
    "expression_gdc":"expression", "expression_cache":"expression",
    "clinical_age":"age", "age_association":"age_association",
    "covariate_adjustment":"adjusted_model", "er_sensitivity":"er_sensitivity",
    "external_geo":"external_replication", "string_network":"network",
    "go_kegg":"enrichment", "module_reduction":"modules",
    "provenance_log":"provenance", "audit_log":"audit",
    "final_report":"report", "provenance_repair":"provenance_repaired",
    "human_review_gate":"human_review",
    "static_dispatch":"controller_state", "goal_planning_overhead":"controller_state",
    "adaptive_planning_overhead":"controller_state", "resource_overuse":"resource_overuse",
}
prerequisites = {
    "expression_gdc":[], "expression_cache":[], "clinical_age":[],
    "age_association":["expression","age"],
    "covariate_adjustment":["age_association"],
    "er_sensitivity":["adjusted_model"],
    "external_geo":["age_association"],
    "string_network":["age_association"],
    "go_kegg":["age_association"],
    "module_reduction":["enrichment"],
    "provenance_log":[], "audit_log":["provenance"],
    "final_report":["provenance"], "provenance_repair":["provenance"],
    "human_review_gate":[], "static_dispatch":[], "goal_planning_overhead":[],
    "adaptive_planning_overhead":[], "resource_overuse":[],
}
governance_actions = {"provenance_log","audit_log","provenance_repair","human_review_gate"}
controller_actions = {"static_dispatch","goal_planning_overhead","adaptive_planning_overhead"}

all_produced = set(produces.values())
for action, reqs in prerequisites.items():
    assert set(reqs).issubset(all_produced)
for name, spec in GOALS.items():
    artifacts=set()
    for action in spec["sequence"]:
        assert set(prerequisites[action]).issubset(artifacts), (name, action)
        artifacts.add(produces[action])
    assert set(spec["required_artifacts"]).issubset(artifacts)

with open(DATA / "action_registry.csv", "w", newline="") as f:
    fields = ["action_id","normalized_cost","prerequisites","produces","category","prohibited_in_clinical_request"]
    w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
    for action,cost in ACTION_COSTS.items():
        category = "governance" if action in governance_actions else ("controller" if action in controller_actions else "molecular")
        w.writerow({
            "action_id":action,
            "normalized_cost":f"{cost:.6f}",
            "prerequisites":"|".join(prerequisites[action]),
            "produces":produces[action],
            "category":category,
            "prohibited_in_clinical_request":int(category=="molecular"),
        })

family_rows = [
    ("clean",160,"Nominal workflow execution","COMPLETE"),
    ("known_source_outage",120,"Primary expression source unavailable; registered cache fallback available","COMPLETE"),
    ("transient_failure",120,"Primary expression action fails once; 60 retry and 60 fallback recovery specifications","COMPLETE"),
    ("evidence_quality",70,"Mapping loss 0.15 for 35 adequate cases and 0.30 for 35 fail-safe cases","35 COMPLETE / 35 FAIL_SAFE"),
    ("provenance_attack",50,"Provenance state corrupted and repair required","COMPLETE"),
    ("prohibited_clinical_request",60,"Out-of-scope treatment request; 25 explicit and 35 implicit patterns","BLOCK"),
    ("unseen_composition",60,"Five held-out compositions of registered actions, 12 scenarios each","COMPLETE"),
    ("irrecoverable_source_loss",60,"Primary source unavailable; fallback present for 24 and absent for 36","24 COMPLETE / 36 FAIL_SAFE"),
    ("resource_stress",60,"Multiple valid routes; lower-cost registered expression route preferred","COMPLETE"),
]
with open(DATA / "scenario_family_definitions.csv", "w", newline="") as f:
    w=csv.writer(f); w.writerow(["family","n","operational_definition","reference_outcome"]); w.writerows(family_rows)


def sha256(path):
    h=hashlib.sha256(); h.update(Path(path).read_bytes()); return h.hexdigest()
files=["controller_input_manifest.csv","reference_policy.csv","canonical_goal_definitions.json","heldout_goal_definitions.json","goal_definitions.json","action_registry.csv","scenario_family_definitions.csv"]
manifest={"benchmark_version":"1.0-integrity-revision","status":"frozen generated benchmark","files":{name:sha256(DATA/name) for name in files}}
with open(DATA/"FREEZE_MANIFEST.json","w") as f:
    json.dump(manifest,f,indent=2)

cnt=Counter(r["reference_outcome"] for r in reference_rows)
assert cnt == {"COMPLETE":629,"BLOCK":60,"FAIL_SAFE":71}
print("Frozen benchmark written:",DATA)
print("Reference outcomes:",dict(cnt))
print("Canonical goal counts:",{g:sum(1 for s in scenarios if s['goal_name']==g) for g in CANONICAL_GOALS})
print("Held-out goal counts:",{g:sum(1 for s in scenarios if s['goal_name']==g) for g in HELDOUT_GOALS})
