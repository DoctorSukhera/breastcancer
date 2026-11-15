#!/usr/bin/env python3
"""Config-driven orchestration of the released molecular-analysis scripts.

The release intentionally does not redistribute the external TCGA/GEO/STRING/
enrichment inputs used by the manuscript. This runner makes that boundary
explicit while providing one dependency-ordered command for users who have
obtained those source files locally.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_INPUTS = [
    "tcga_expression",
    "tcga_clinical",
    "genage",
    "geo_series_matrix",
    "geo_annotation",
    "geo_metadata",
    "string_edges",
    "string_mapping",
    "go_gene_sets",
    "kegg_gene_sets",
]


def _resolve(value: str, base: Path) -> Path:
    p = Path(value).expanduser()
    if not p.is_absolute():
        p = base / p
    return p.resolve()


def load_config(path: Path) -> dict:
    cfg = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(cfg, dict):
        raise ValueError("Molecular config must be a JSON object")
    cfg.setdefault("inputs", {})
    cfg.setdefault("columns", {})
    cfg.setdefault("settings", {})
    return cfg


def read_header(path: Path) -> list[str]:
    sep = "\t" if path.suffix.lower() in {".tsv", ".txt"} else ","
    return list(pd.read_csv(path, sep=sep, nrows=0).columns)


def validate_config(cfg: dict, config_path: Path, require_outside_repo: bool = False) -> dict:
    base = config_path.parent.resolve()
    inputs = cfg.get("inputs", {})
    missing_keys = [k for k in REQUIRED_INPUTS if not inputs.get(k)]
    if missing_keys:
        raise ValueError("Missing required molecular input key(s): " + ", ".join(missing_keys))

    resolved = {k: _resolve(inputs[k], base) for k in REQUIRED_INPUTS}
    if inputs.get("enrichment_background"):
        resolved["enrichment_background"] = _resolve(inputs["enrichment_background"], base)
    missing_files = [f"{k}={p}" for k, p in resolved.items() if not p.is_file()]
    if missing_files:
        raise FileNotFoundError("Missing molecular input file(s):\n  " + "\n  ".join(missing_files))

    output_value = cfg.get("output_dir")
    if not output_value:
        raise ValueError("Molecular config requires output_dir")
    outdir = _resolve(output_value, base)
    if require_outside_repo:
        try:
            outdir.relative_to(ROOT.resolve())
        except ValueError:
            pass
        else:
            raise ValueError(
                "When invoked from run_all.py, molecular output_dir must be outside the release repository "
                "so external-data-derived outputs do not alter the frozen release manifest."
            )

    cols = {
        "sample_col": "sample_id",
        "age_col": "age",
        "er_col": "ER",
        "pr_col": "PR",
        "her2_col": "HER2",
        "stage_col": "stage",
        "gene_column": None,
        "geo_probe_col": "probe_id",
        "geo_symbol_col": "gene_symbol",
        "geo_sample_col": "sample_id",
        "geo_age_col": "age",
    }
    cols.update(cfg.get("columns", {}))

    # Validate small schemas before starting any stage. Large expression files
    # are inspected header-only here and loaded only by their analysis stage.
    tcga_clin = set(read_header(resolved["tcga_clinical"]))
    needed_clin = {cols[k] for k in ["sample_col", "age_col", "er_col", "pr_col", "her2_col", "stage_col"]}
    absent = sorted(needed_clin - tcga_clin)
    if absent:
        raise ValueError("TCGA clinical file lacks required column(s): " + ", ".join(absent))

    geo_ann = set(read_header(resolved["geo_annotation"]))
    absent = sorted({cols["geo_probe_col"], cols["geo_symbol_col"]} - geo_ann)
    if absent:
        raise ValueError("GEO annotation file lacks required column(s): " + ", ".join(absent))
    geo_meta = set(read_header(resolved["geo_metadata"]))
    absent = sorted({cols["geo_sample_col"], cols["geo_age_col"]} - geo_meta)
    if absent:
        raise ValueError("GEO metadata file lacks required column(s): " + ", ".join(absent))

    string_edges = set(read_header(resolved["string_edges"]))
    absent = sorted({"protein1", "protein2", "combined_score"} - string_edges)
    if absent:
        raise ValueError("STRING edge file lacks required column(s): " + ", ".join(absent))
    if len(read_header(resolved["string_mapping"])) < 2:
        raise ValueError("STRING mapping file requires at least two columns: protein ID and gene symbol")

    return {"inputs": resolved, "columns": cols, "settings": cfg.get("settings", {}), "outdir": outdir}


def run(cmd: list[str]) -> None:
    print("\n>>>", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=ROOT, check=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", type=Path, help="JSON configuration containing external molecular input paths")
    ap.add_argument("--check-only", action="store_true", help="Validate the config and input schemas without running analyses")
    ap.add_argument("--release-status", action="store_true", help="Report the bundled-release molecular reproduction boundary")
    ap.add_argument("--require-outside-repo", action="store_true", help=argparse.SUPPRESS)
    args = ap.parse_args()

    if args.release_status:
        print(
            "MOLECULAR REPRODUCTION STATUS: EXTERNAL INPUTS REQUIRED\n"
            "The release ships executable molecular-analysis code but does not redistribute the manuscript's "
            "TCGA/GEO/STRING/GO/KEGG source files. run_all.py therefore does not silently claim a molecular rerun.\n"
            "To execute the molecular pipeline, supply: python run_all.py --molecular-config /path/to/molecular_config.json"
        )
        return 0
    if args.config is None:
        ap.error("--config is required unless --release-status is used")

    config_path = args.config.expanduser().resolve()
    cfg = load_config(config_path)
    v = validate_config(cfg, config_path, args.require_outside_repo)
    inp, c, settings, out = v["inputs"], v["columns"], v["settings"], v["outdir"]
    print("MOLECULAR INPUT VALIDATION: PASS")
    print("Output directory:", out)
    if args.check_only:
        return 0

    out.mkdir(parents=True, exist_ok=True)
    tcga = out / "01_tcga"
    external = out / "02_external_replication.csv"
    er = out / "03_er_stratified.csv"
    string_dir = out / "04_string"
    enrich_dir = out / "05_enrichment"
    perm = out / "06_permutation_counts.csv"
    perm_summary = out / "06_permutation_summary.json"
    boot = out / "07_candidate_bootstrap.csv"
    complete_tables = out / "08_complete_tables"

    cmd = [sys.executable, "analysis/01_tcga_age_association.py",
           "--expression", str(inp["tcga_expression"]), "--clinical", str(inp["tcga_clinical"]),
           "--genage", str(inp["genage"]), "--sample-col", c["sample_col"], "--age-col", c["age_col"],
           "--er-col", c["er_col"], "--pr-col", c["pr_col"], "--her2-col", c["her2_col"],
           "--stage-col", c["stage_col"], "--outdir", str(tcga)]
    if c.get("gene_column"):
        cmd += ["--gene-column", str(c["gene_column"])]
    run(cmd)

    adj = pd.read_csv(tcga / "tcga_adjusted_age_association.csv")
    if "fdr_adjusted" not in adj.columns or "gene" not in adj.columns:
        raise RuntimeError("TCGA adjusted output lacks gene/fdr_adjusted columns")
    adjusted_sig = adj.loc[pd.to_numeric(adj["fdr_adjusted"], errors="coerce") < 0.05, ["gene"]].copy()
    adjusted_sig_path = out / "adjusted_significant_genes.csv"
    adjusted_sig.to_csv(adjusted_sig_path, index=False)

    run([sys.executable, "analysis/02_external_replication.py",
         "--series-matrix", str(inp["geo_series_matrix"]), "--annotation", str(inp["geo_annotation"]),
         "--metadata", str(inp["geo_metadata"]), "--locked", str(tcga / "locked_top40_candidates.csv"),
         "--probe-col", c["geo_probe_col"], "--symbol-col", c["geo_symbol_col"],
         "--sample-col", c["geo_sample_col"], "--age-col", c["geo_age_col"], "--out", str(external)])

    run([sys.executable, "analysis/03_er_stratified_sensitivity.py",
         "--expression", str(inp["tcga_expression"]), "--clinical", str(inp["tcga_clinical"]),
         "--candidates", str(adjusted_sig_path), "--sample-col", c["sample_col"], "--age-col", c["age_col"],
         "--er-col", c["er_col"], "--out", str(er)])

    run([sys.executable, "analysis/04_string_network.py",
         "--edges", str(inp["string_edges"]), "--mapping", str(inp["string_mapping"]),
         "--genes", str(adjusted_sig_path), "--outdir", str(string_dir)])

    enrichment_genes = string_dir / "string_node_centrality_700.csv"
    enrich_cmd=[sys.executable, "analysis/05_enrichment_analysis.py",
         "--genes", str(enrichment_genes), "--gene-column", "gene",
         "--go-gene-sets", str(inp["go_gene_sets"]),
         "--kegg-gene-sets", str(inp["kegg_gene_sets"]),
         "--go-library-name", str(settings.get("go_library_name", "GO_Biological_Process_snapshot")),
         "--kegg-library-name", str(settings.get("kegg_library_name", "KEGG_Human_snapshot")),
         "--outdir", str(enrich_dir)]
    if inp.get("enrichment_background"):
        enrich_cmd += ["--background", str(inp["enrichment_background"])]
    run(enrich_cmd)
    run([sys.executable, "analysis/05_enrichment_redundancy.py",
         "--enrichment", str(enrich_dir / "enrichment_computed.csv"),
         "--top", str(int(settings.get("enrichment_top", 180))),
         "--jaccard", str(float(settings.get("enrichment_jaccard", 0.40))),
         "--outdir", str(enrich_dir)])

    run([sys.executable, "analysis/06_permutation_bootstrap.py",
         "--expression", str(inp["tcga_expression"]), "--clinical", str(inp["tcga_clinical"]),
         "--genes", str(inp["genage"]), "--sample-col", c["sample_col"], "--age-col", c["age_col"],
         "--strata", c["er_col"], "--permutations", str(int(settings.get("permutations", 500))),
         "--seed", str(int(settings.get("permutation_seed", 42))), "--out", str(perm),
         "--summary", str(perm_summary)])

    run([sys.executable, "analysis/07_candidate_bootstrap.py",
         "--expression", str(inp["tcga_expression"]), "--clinical", str(inp["tcga_clinical"]),
         "--candidates", str(tcga / "locked_top40_candidates.csv"), "--sample-col", c["sample_col"],
         "--age-col", c["age_col"], "--resamples", str(int(settings.get("bootstrap_resamples", 1000))),
         "--seed", str(int(settings.get("bootstrap_seed", 42))), "--out", str(boot)])

    run([sys.executable, "analysis/08_compile_molecular_tables.py",
         "--molecular-dir", str(out), "--outdir", str(complete_tables)])

    manifest = {
        "status": "complete",
        "config": str(config_path),
        "output_dir": str(out),
        "external_inputs": {k: str(v) for k, v in inp.items()},
        "derived_outputs": {
            "tcga_dir": str(tcga),
            "adjusted_significant_genes": str(adjusted_sig_path),
            "external_replication": str(external),
            "er_stratified": str(er),
            "string_dir": str(string_dir),
            "enrichment_dir": str(enrich_dir),
            "permutation_counts": str(perm),
            "permutation_summary": str(perm_summary),
            "candidate_bootstrap": str(boot),
            "complete_molecular_tables_dir": str(complete_tables),
            "complete_molecular_tables_manifest": str(complete_tables / "MOLECULAR_RESULT_TABLES_MANIFEST.json"),
        },
        "settings": settings,
    }
    (out / "MOLECULAR_RUN_MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("\nMOLECULAR REPRODUCTION WORKFLOW: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
