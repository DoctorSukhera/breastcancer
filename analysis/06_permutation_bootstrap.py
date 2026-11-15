#!/usr/bin/env python3
"""Stratified age-label permutation test for the global age-association burden.

The manuscript-specified primary design permutes age labels within ER strata,
including an explicit Unknown ER category. Alternative stratification columns
can still be supplied explicitly with --strata for sensitivity analyses, but
ER-only stratification is the reproducible default.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from common import load_expression, read_table, bh


MISSING_CATEGORY_TOKENS = {
    "", "na", "n/a", "nan", "none", "null", "not available",
    "[not available]", "not reported", "[not reported]",
    "not evaluated", "[not evaluated]", "indeterminate",
}


def retain_missing_as_category(series: pd.Series, label: str = "Unknown") -> pd.Series:
    """Normalize missing/placeholder categorical values to an explicit label."""
    out = series.astype("string").str.strip()
    low = out.str.lower()
    mask = out.isna() | low.isin(MISSING_CATEGORY_TOKENS)
    return out.mask(mask, label).astype(str)


def parse_strata(value: str) -> list[str]:
    cols = [x.strip() for x in str(value).split(',') if x.strip()]
    if not cols:
        raise ValueError("At least one stratification column is required")
    return cols


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--expression', required=True)
    ap.add_argument('--clinical', required=True)
    ap.add_argument('--genes', required=True)
    ap.add_argument('--sample-col', default='sample_id')
    ap.add_argument('--age-col', default='age')
    ap.add_argument(
        '--strata', default='ER',
        help='Comma-separated permutation strata. Default ER matches the manuscript primary analysis.'
    )
    ap.add_argument('--missing-category-label', default='Unknown')
    ap.add_argument('--permutations', type=int, default=500)
    ap.add_argument('--seed', type=int, default=42)
    ap.add_argument('--out', default='results/permutation_counts.csv')
    ap.add_argument('--summary', default=None, help='Optional JSON audit summary path')
    args = ap.parse_args()

    strata_cols = parse_strata(args.strata)
    expr = load_expression(args.expression)
    clin = read_table(args.clinical).copy()
    clin[args.sample_col] = clin[args.sample_col].astype(str)
    clin = clin.set_index(args.sample_col)

    missing_cols = [c for c in [args.age_col, *strata_cols] if c not in clin.columns]
    if missing_cols:
        raise KeyError(f"Required clinical column(s) not found: {', '.join(missing_cols)}")

    for c in strata_cols:
        clin[c] = retain_missing_as_category(clin[c], args.missing_category_label)

    genes = read_table(args.genes).iloc[:, 0].astype(str).str.upper().str.strip().tolist()
    ids = [s for s in expr.columns.astype(str) if s in clin.index]
    if not ids:
        raise ValueError('No expression samples match the clinical sample IDs')

    age = pd.to_numeric(clin.loc[ids, args.age_col], errors='coerce')
    strata_frame = clin.loc[ids, strata_cols].astype(str)
    strata = strata_frame.agg('|'.join, axis=1)
    rng = np.random.default_rng(args.seed)

    def count_sig(a: pd.Series) -> int:
        ps = []
        for g in genes:
            if g not in expr.index:
                ps.append(np.nan)
                continue
            y = pd.to_numeric(expr.loc[g, ids], errors='coerce')
            m = a.notna() & y.notna()
            ps.append(spearmanr(a[m], y[m]).pvalue if int(m.sum()) >= 3 else np.nan)
        return int(np.nansum(bh(ps) < .05))

    obs = count_sig(age)
    counts = []
    grouped_indices = list(strata.groupby(strata, sort=True).groups.items())
    for _ in range(args.permutations):
        perm = age.copy()
        for _, ix in grouped_indices:
            perm.loc[ix] = rng.permutation(age.loc[ix].to_numpy())
        counts.append(count_sig(perm))

    empirical_p = (1 + sum(c >= obs for c in counts)) / (args.permutations + 1)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({
        'permutation': range(1, args.permutations + 1),
        'significant_genes': counts,
    }).to_csv(out_path, index=False)

    group_sizes = {str(k): int(len(v)) for k, v in grouped_indices}
    summary = {
        'observed_fdr_significant_genes': int(obs),
        'n_permutations': int(args.permutations),
        'empirical_p_add_one': float(empirical_p),
        'seed': int(args.seed),
        'strata_columns': strata_cols,
        'missing_category_label': args.missing_category_label,
        'n_matched_samples': int(len(ids)),
        'n_strata': int(len(grouped_indices)),
        'stratum_sizes': group_sizes,
        'primary_manuscript_design': strata_cols == ['ER'],
    }
    summary_path = Path(args.summary) if args.summary else out_path.with_name(out_path.stem + '_summary.json')
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + '\n', encoding='utf-8')

    print(summary)


if __name__ == '__main__':
    main()
