# Complete derived molecular result tables

The compact CSV files under `data/source_tables/` exist to regenerate Figures 2–4 and are **not** intended to be the complete molecular analysis record. A genuine molecular rerun now creates a separate derived-result package under:

`<molecular output>/08_complete_tables/`

This package contains gene-, term-, network-, and permutation-level derived results only. It does **not** contain patient/sample-level TCGA or GEO records.

## Standardized tables

| Table | Contents |
|---|---|
| `M1_tcga_all_curated_gene_statistics.csv` | Every expression-testable curated gene with unadjusted Spearman statistics, HC3-adjusted age coefficient/CI/P/FDR, quadratic-age sensitivity, and significance flags. |
| `M2_locked_candidates_complete_multi_evidence.csv` | Every prespecified locked candidate, including TCGA adjusted statistics, external replication status/statistics, ER-stratified correlations/heterogeneity, candidate bootstrap stability, and score-700 STRING centrality when available. |
| `M3_string_node_metrics_all_thresholds.csv` | Every candidate node at STRING required scores 400, 700, and 900 with degree, degree rank, betweenness, and closeness. Isolates are retained. |
| `M4_string_edges_all_thresholds.csv` | Every retained candidate gene-gene STRING edge at each tested confidence threshold, with combined score. |
| `M5_enrichment_all_terms.csv` | Every enrichment result computed from the frozen GO/KEGG gene-set snapshots, including the FDR-significance flag. |
| `M6_enrichment_cluster_membership.csv` | Exact membership of the top significant terms used in Jaccard clustering, including representative-term flags. |
| `M7_permutation_null_distribution.csv` | The complete finite stratified age-label permutation null distribution. |
| `M8_molecular_result_table_inventory.csv` | File-level provenance inventory with descriptions, row/column counts and SHA-256 hashes. |

Additional stage-level exports include the complete FDR-significant enrichment subset, top-20 STRING hubs at each threshold, all node-removal AUC replicates, the TCGA covariate-missingness audit, and the permutation-design audit JSON.

## Historical-result boundary

The release does not redistribute the patient-level TCGA/GEO inputs required to regenerate these full tables, and historical full derived CSVs were not recoverable as standalone release artifacts. Therefore the repository does **not** fabricate unobserved rows to make the compact figure tables appear complete. The standardized full table package is generated only from an actual molecular rerun using user-obtained source data via:

```bash
python analysis/run_molecular_pipeline.py --config /path/to/molecular_config.json
```

The resulting `MOLECULAR_RESULT_TABLES_MANIFEST.json` records row counts and deterministic hashes for the standardized tables.
