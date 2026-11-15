#!/usr/bin/env python3
"""Synchronize Figure 5 controller summary from authoritative generated benchmark results.

This script is intentionally a projection, not an independent numerical source.  It
maps results/generated/benchmark_controller_summary.csv into the compact schema
consumed by scripts/generate_figures_2_6.py.
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "results" / "generated" / "benchmark_controller_summary.csv"
TARGET = ROOT / "data" / "source_tables" / "Figure5_controller_summary.csv"

SYSTEM_ORDER = ["Static workflow", "Goal planner", "Adaptive planner", "Bounded controller"]
COLUMN_MAP = {
    "policy_conformance": "policy",
    "action_appropriateness": "action",
    "safety_conformance": "safety",
    "provenance_conformance": "provenance",
    "escalation_conformance": "escalation",
    "resource_stewardship": "stewardship",
    "mean_cost": "mean_cost",
}
OUTPUT_COLUMNS = ["system", "policy", "action", "safety", "provenance", "escalation", "stewardship", "mean_cost"]


def projected_table(source: Path = SOURCE) -> pd.DataFrame:
    df = pd.read_csv(source)
    required = {"system", *COLUMN_MAP.keys()}
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"benchmark controller summary missing required columns: {missing}")

    rows = df[df["system"].isin(SYSTEM_ORDER)].copy()
    if set(rows["system"]) != set(SYSTEM_ORDER) or len(rows) != len(SYSTEM_ORDER):
        raise ValueError(
            "benchmark controller summary must contain exactly one row for each Figure 5 controller: "
            + ", ".join(SYSTEM_ORDER)
        )
    order = {name: i for i, name in enumerate(SYSTEM_ORDER)}
    rows["_order"] = rows["system"].map(order)
    rows = rows.sort_values("_order").drop(columns="_order")
    rows = rows[["system", *COLUMN_MAP.keys()]].rename(columns=COLUMN_MAP)
    return rows[OUTPUT_COLUMNS].reset_index(drop=True)


def main() -> int:
    table = projected_table()
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(TARGET, index=False, lineterminator="\n", float_format="%.15g")
    print(f"Figure 5 controller summary synchronized from {SOURCE.relative_to(ROOT)} -> {TARGET.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
