#!/usr/bin/env python3
"""Schema adapter for the prespecified TCGA-BLCA held-out transfer protocol.

The adapter performs schema harmonization only.  It never changes controller
rules, reference policies, benchmark thresholds or action costs.

Supported adapter responsibilities (matching the manuscript contract):
- delimiter/format ingestion;
- expression orientation detection (gene x sample or sample x gene);
- clinical column-name normalization and sample-ID resolution;
- explicit missing-value parsing;
- gene-identifier standardization, with optional Ensembl->symbol mapping;
- exact or TCGA participant-level sample linkage;
- fail-safe HUMAN_REVIEW output when required fields/linkage are ambiguous.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable

import pandas as pd

MISSING_TOKENS = {
    "", "na", "n/a", "nan", "none", "null", "not available", "not reported",
    "not evaluated", "unknown", "--", "[not available]", "[not reported]",
}
SAMPLE_ALIASES = (
    "sample_id", "sample", "submitter_id", "case_submitter_id", "case_id",
    "patient_id", "participant_id", "barcode", "bcr_patient_barcode",
)
ENSEMBL_RE = re.compile(r"^ENSG\d+(?:\.\d+)?$", re.I)
TCGA_RE = re.compile(r"^TCGA-[A-Z0-9]{2}-[A-Z0-9]{4}(?:-.+)?$", re.I)


def _sep(path: Path) -> str:
    return "\t" if path.suffix.lower() in {".tsv", ".txt", ".tab"} else ","


def _canon_col(value: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "_", str(value).strip().lower()).strip("_")
    return s or "unnamed"


def _normalize_headers(df: pd.DataFrame) -> pd.DataFrame:
    new = [_canon_col(c) for c in df.columns]
    if len(new) != len(set(new)):
        dup = sorted({x for x in new if new.count(x) > 1})
        raise ValueError(f"Column-name normalization creates duplicates: {dup}")
    out = df.copy()
    out.columns = new
    return out


def _parse_missing(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    out = df.copy()
    n = 0
    for c in out.columns:
        if out[c].dtype == object or pd.api.types.is_string_dtype(out[c]):
            s = out[c].astype("string")
            mask = s.str.strip().str.lower().isin(MISSING_TOKENS)
            n += int(mask.sum())
            out.loc[mask, c] = pd.NA
    return out, n


def _read(path: Path, normalize_headers: bool = False) -> tuple[pd.DataFrame, int]:
    df = pd.read_csv(path, sep=_sep(path), dtype=None, keep_default_na=False, na_filter=False)
    if normalize_headers:
        df = _normalize_headers(df)
    df, n_missing = _parse_missing(df)
    return df, n_missing


def _resolve_sample_col(clinical: pd.DataFrame, requested: str | None) -> str:
    if requested:
        c = _canon_col(requested)
        if c not in clinical.columns:
            raise ValueError(f"Requested clinical sample column {requested!r} not found after normalization")
        return c
    found = [c for c in SAMPLE_ALIASES if c in clinical.columns]
    if len(found) == 1:
        return found[0]
    if not found:
        raise ValueError("No unambiguous clinical sample/patient identifier column found")
    raise ValueError(f"Multiple candidate clinical identifier columns found: {found}")


def _clean_id(x) -> str | None:
    if pd.isna(x):
        return None
    s = str(x).strip()
    return s or None


def _participant_id(x: str) -> str:
    s = str(x).strip().upper()
    if not TCGA_RE.match(s):
        raise ValueError(f"Non-TCGA barcode encountered under tcga_participant linkage: {x!r}")
    return "-".join(s.split("-")[:3])


def _link_id(x: str, mode: str) -> str:
    s = str(x).strip()
    return _participant_id(s) if mode == "tcga_participant" else s


def _detect_link_mode(expr_ids: Iterable[str], clinical_ids: Iterable[str], requested: str) -> tuple[str, int]:
    e = [x for x in (_clean_id(v) for v in expr_ids) if x]
    c = [x for x in (_clean_id(v) for v in clinical_ids) if x]
    if requested != "auto":
        em = {_link_id(x, requested) for x in e}
        cm = {_link_id(x, requested) for x in c}
        return requested, len(em & cm)
    exact = len(set(e) & set(c))
    if exact:
        return "exact", exact
    if e and c and all(TCGA_RE.match(x.upper()) for x in e + c):
        ep = {_participant_id(x) for x in e}
        cp = {_participant_id(x) for x in c}
        n = len(ep & cp)
        if n:
            return "tcga_participant", n
    return "exact", 0


def _orientation_scores(expr: pd.DataFrame, clinical_ids: list[str], requested_expr_sample_col: str | None = None):
    clinical = [str(x).strip() for x in clinical_ids if _clean_id(x)]
    cset = set(clinical)
    tcga_mode = bool(clinical) and all(TCGA_RE.match(x.upper()) for x in clinical)
    cpart = {_participant_id(x) for x in clinical} if tcga_mode else set()

    def matched(v):
        if not _clean_id(v):
            return False
        x = str(v).strip()
        if x in cset:
            return True
        if tcga_mode and TCGA_RE.match(x.upper()):
            return _participant_id(x) in cpart
        return False

    # gene x sample: sample identifiers live in expression column headers.
    gxs = sum(matched(c) for c in expr.columns)
    # sample x gene: sample identifiers live in one expression column.
    value_scores = {}
    for c in expr.columns:
        vals = {_clean_id(v) for v in expr[c].tolist()}
        vals.discard(None)
        value_scores[c] = sum(matched(v) for v in vals)
    if requested_expr_sample_col:
        matches = [c for c in expr.columns if _canon_col(c) == _canon_col(requested_expr_sample_col)]
        if len(matches) != 1:
            raise ValueError(f"Expression sample column {requested_expr_sample_col!r} cannot be resolved unambiguously")
        sxg_col = matches[0]
    else:
        sxg_col = max(value_scores, key=value_scores.get)
    sxg = value_scores.get(sxg_col, 0)
    return gxs, sxg, sxg_col

def _detect_orientation(expr: pd.DataFrame, clinical_ids: list[str], requested: str, requested_expr_sample_col: str | None):
    if requested in {"gene_by_sample", "sample_by_gene"}:
        gxs, sxg, scol = _orientation_scores(expr, clinical_ids, requested_expr_sample_col)
        return requested, scol, gxs, sxg
    gxs, sxg, scol = _orientation_scores(expr, clinical_ids, requested_expr_sample_col)
    if gxs <= 0 and sxg <= 0:
        raise ValueError("Expression orientation cannot be resolved from clinical sample-ID overlap")
    if gxs == sxg:
        raise ValueError(f"Expression orientation is ambiguous (gene_by_sample score={gxs}, sample_by_gene score={sxg})")
    return ("gene_by_sample" if gxs > sxg else "sample_by_gene"), scol, gxs, sxg


def _infer_gene_namespace(values: Iterable[str], requested: str) -> str:
    if requested != "auto":
        return requested
    vals = [str(v).strip() for v in values if _clean_id(v)]
    if not vals:
        raise ValueError("No gene identifiers available for namespace inference")
    frac = sum(bool(ENSEMBL_RE.match(v)) for v in vals) / len(vals)
    return "ensembl" if frac >= 0.8 else "symbol"


def _standardize_gene_ids(values: pd.Series, namespace: str) -> pd.Series:
    s = values.astype("string").str.strip().str.upper()
    if namespace == "ensembl":
        s = s.str.replace(r"\.\d+$", "", regex=True)
    return s


def _load_gene_mapping(path: Path, source_col: str, target_col: str, namespace: str) -> dict[str, str]:
    m, _ = _read(path, normalize_headers=True)
    sc, tc = _canon_col(source_col), _canon_col(target_col)
    if sc not in m.columns or tc not in m.columns:
        raise ValueError(f"Gene-mapping table must contain {source_col!r} and {target_col!r}")
    src = _standardize_gene_ids(m[sc], namespace)
    tgt = m[tc].astype("string").str.strip().str.upper()
    tmp = pd.DataFrame({"src": src, "tgt": tgt}).dropna().drop_duplicates()
    amb = tmp.groupby("src").tgt.nunique()
    bad = amb[amb > 1]
    if not bad.empty:
        raise ValueError(f"Ambiguous gene mappings for {len(bad)} identifiers")
    return tmp.drop_duplicates("src").set_index("src").tgt.to_dict()


def _write_audit(out: Path, audit: dict):
    out.mkdir(parents=True, exist_ok=True)
    (out / "adapter_audit.json").write_text(json.dumps(audit, indent=2, sort_keys=True), encoding="utf-8")
    pd.DataFrame([audit]).to_csv(out / "adapter_report.csv", index=False)


def adapt(args) -> dict:
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    audit = {
        "status": "HUMAN_REVIEW",
        "dataset": "TCGA-BLCA",
        "expression_file": str(Path(args.expression).resolve()),
        "clinical_file": str(Path(args.clinical).resolve()),
        "unresolved_fields": [],
    }
    try:
        clinical, clinical_missing = _read(Path(args.clinical), normalize_headers=True)
        sample_col = _resolve_sample_col(clinical, args.sample_col)
        clinical_ids = [_clean_id(v) for v in clinical[sample_col]]
        if any(v is None for v in clinical_ids):
            raise ValueError(f"Clinical identifier column {sample_col!r} contains missing IDs")
        if pd.Series(clinical_ids).duplicated().any():
            raise ValueError(f"Clinical identifier column {sample_col!r} contains duplicate IDs")

        # Expression headers are preserved initially because gene-by-sample sample IDs live in headers.
        expr_raw, expr_missing = _read(Path(args.expression), normalize_headers=False)
        if expr_raw.empty or expr_raw.shape[1] < 2:
            raise ValueError("Expression table must contain at least two columns")
        orientation, expr_sample_col_guess, score_gxs, score_sxg = _detect_orientation(
            expr_raw, clinical_ids, args.orientation, args.expression_sample_col
        )

        if orientation == "gene_by_sample":
            gene_col = args.gene_col or expr_raw.columns[0]
            if gene_col not in expr_raw.columns:
                # allow normalized spelling of a raw header
                matches = [c for c in expr_raw.columns if _canon_col(c) == _canon_col(gene_col)]
                if len(matches) != 1:
                    raise ValueError(f"Gene identifier column {gene_col!r} cannot be resolved")
                gene_col = matches[0]
            gene_values = expr_raw[gene_col]
            expression = expr_raw.drop(columns=[gene_col]).copy()
            expression.index = gene_values
        else:
            # Preserve gene-column headers verbatim: in sample-by-gene matrices the
            # headers are gene identifiers and must not be snake-case normalized.
            if args.expression_sample_col:
                matches = [c for c in expr_raw.columns if _canon_col(c) == _canon_col(args.expression_sample_col)]
                if len(matches) != 1:
                    raise ValueError(f"Expression sample column {args.expression_sample_col!r} cannot be resolved")
                sample_col_expr = matches[0]
            else:
                sample_col_expr = expr_sample_col_guess
            sample_values = expr_raw[sample_col_expr].map(_clean_id)
            if sample_values.isna().any() or sample_values.duplicated().any():
                raise ValueError("Expression sample identifier column contains missing or duplicate IDs")
            data = expr_raw.drop(columns=[sample_col_expr]).copy()
            data.index = sample_values
            # transpose to canonical gene x sample representation
            expression = data.T
            expression.index.name = "gene_id"
            gene_values = pd.Series(expression.index, index=expression.index)

        namespace = _infer_gene_namespace(gene_values, args.gene_namespace)
        std_gene = _standardize_gene_ids(pd.Series(expression.index, index=expression.index), namespace)
        expression.index = list(std_gene)
        expression.index.name = "gene_id"
        n_unmapped = 0
        output_namespace = namespace
        if args.gene_mapping:
            mapping = _load_gene_mapping(Path(args.gene_mapping), args.mapping_source_col, args.mapping_target_col, namespace)
            mapped = pd.Series(expression.index, index=expression.index).map(mapping)
            n_unmapped = int(mapped.isna().sum())
            expression = expression.loc[~mapped.isna()].copy()
            expression.index = mapped.dropna().astype(str).tolist()
            expression.index.name = "gene_id"
            output_namespace = "symbol"

        # Coerce expression values to numeric after identifiers are separated.
        expression = expression.apply(pd.to_numeric, errors="coerce")
        # Duplicate standardized genes are collapsed deterministically by median.
        expression = expression.groupby(level=0, sort=True).median(numeric_only=True)

        link_mode, link_overlap = _detect_link_mode(expression.columns, clinical_ids, args.sample_link_mode)
        if link_overlap <= 0:
            raise ValueError("No unambiguous expression/clinical sample overlap found")

        expr_link = [_link_id(str(x), link_mode) for x in expression.columns]
        if pd.Series(expr_link).duplicated().any():
            raise ValueError("Sample linkage maps multiple expression columns to the same clinical identifier")
        clin_link = [_link_id(str(x), link_mode) for x in clinical_ids]
        if pd.Series(clin_link).duplicated().any():
            raise ValueError("Sample linkage maps multiple clinical rows to the same identifier")

        e_map = dict(zip(expr_link, expression.columns))
        c_map = dict(zip(clin_link, range(len(clinical))))
        common = sorted(set(e_map) & set(c_map))
        if not common:
            raise ValueError("No aligned samples remain after linkage")

        aligned_expr = expression.loc[:, [e_map[x] for x in common]].copy()
        aligned_expr.columns = common
        aligned_clin = clinical.iloc[[c_map[x] for x in common]].copy()
        aligned_clin[sample_col] = common
        aligned_clin = aligned_clin.set_index(sample_col).loc[common].reset_index()

        aligned_expr.to_csv(out / "expression_common_schema.csv")
        aligned_clin.to_csv(out / "clinical_common_schema.csv", index=False)

        audit.update({
            "status": "PASS",
            "unresolved_fields": [],
            "expression_orientation": orientation,
            "orientation_gene_by_sample_overlap": int(score_gxs),
            "orientation_sample_by_gene_overlap": int(score_sxg),
            "clinical_sample_column": sample_col,
            "sample_link_mode": link_mode,
            "gene_namespace_input": namespace,
            "gene_namespace_output": output_namespace,
            "gene_mapping_file": str(Path(args.gene_mapping).resolve()) if args.gene_mapping else "",
            "n_expression_genes": int(expression.shape[0]),
            "n_expression_samples": int(expression.shape[1]),
            "n_clinical_rows": int(len(clinical)),
            "n_aligned_samples": int(len(common)),
            "n_unmapped_genes_dropped": int(n_unmapped),
            "n_missing_tokens_expression": int(expr_missing),
            "n_missing_tokens_clinical": int(clinical_missing),
        })
        _write_audit(out, audit)
        return audit
    except Exception as exc:
        audit["unresolved_fields"] = [str(exc)]
        _write_audit(out, audit)
        raise


def build_parser():
    ap = argparse.ArgumentParser()
    ap.add_argument("--expression", required=True, help="BLCA expression table (gene x sample or sample x gene)")
    ap.add_argument("--clinical", required=True, help="BLCA clinical table")
    ap.add_argument("--sample-col", default=None, help="Clinical sample/patient ID column; auto-resolved from standard aliases if omitted")
    ap.add_argument("--expression-sample-col", default=None, help="Sample-ID column for sample x gene expression input")
    ap.add_argument("--gene-col", default=None, help="Gene-ID column for gene x sample expression input")
    ap.add_argument("--orientation", choices=["auto", "gene_by_sample", "sample_by_gene"], default="auto")
    ap.add_argument("--sample-link-mode", choices=["auto", "exact", "tcga_participant"], default="auto")
    ap.add_argument("--gene-namespace", choices=["auto", "symbol", "ensembl"], default="auto")
    ap.add_argument("--gene-mapping", default=None, help="Optional mapping CSV/TSV, e.g. Ensembl -> gene symbol")
    ap.add_argument("--mapping-source-col", default="ensembl_id")
    ap.add_argument("--mapping-target-col", default="gene_symbol")
    ap.add_argument("--outdir", default="data/adapted_blca")
    return ap


def main():
    args = build_parser().parse_args()
    try:
        audit = adapt(args)
    except Exception as exc:
        print(f"HUMAN_REVIEW: {exc}")
        raise SystemExit(2)
    print(f"Adapter PASS: {audit['n_aligned_samples']} aligned samples; orientation={audit['expression_orientation']}; linkage={audit['sample_link_mode']}")


if __name__ == "__main__":
    main()
