# Manuscript-to-repository map

This table identifies the executable artifact supporting each major reproducibility claim in the revised manuscript.

| Manuscript component | Repository artifact |
|---|---|
| TCGA-BRCA age association / HC3 adjustment | `analysis/01_tcga_age_association.py` |
| GSE42568 directional replication | `analysis/02_external_replication.py` |
| ER-stratified sensitivity / heterogeneity | `analysis/03_er_stratified_sensitivity.py` |
| STRING threshold, degree-rank, overlap and removal sensitivity | `analysis/04_string_network.py` |
| GO/KEGG over-representation analysis | `analysis/05_enrichment_analysis.py` |
| Enrichment redundancy reduction | `analysis/05_enrichment_redundancy.py` |
| Stratified age-label permutation | `analysis/06_permutation_bootstrap.py` |
| Candidate case-resampling stability | `analysis/07_candidate_bootstrap.py` |
| Complete derived molecular result tables | `analysis/08_compile_molecular_tables.py`, `docs/MOLECULAR_RESULT_TABLES.md` |
| Frozen 760-scenario benchmark | `benchmark/build_frozen_inputs.py`, `data/frozen/` |
| Bounded/static/goal/adaptive controller execution | `benchmark/controller.py`, `benchmark/run_benchmark.py` |
| Programmatic metric evaluation | `benchmark/evaluator.py`, `docs/METRICS.md` |
| Conventional deterministic comparator | `benchmark/run_deterministic_baseline.py` |
| Component ablation | `benchmark/ablation_controller.py`, `benchmark/run_ablation.py` |
| Finite-benchmark paired effects / family sensitivity | `benchmark/analyze_results.py` |
| Reference-policy isolation checks | `benchmark/validate_package.py`, `tests/test_invariants.py` |
| Restricted LLM future-comparator protocol | `llm/restricted_llm_protocol.py` |
| Prespecified TCGA-BLCA adapter | `adapters/tcga_blca_adapter.py`, `docs/BLCA_TRANSFER_ADAPTER.md` |
| Figure 1 | `scripts/generate_figure1.py` |
| Figures 2–6 | `scripts/generate_figures_2_6.py`, `data/source_tables/` |
| Full reproducibility run | `run_all.py` |

## Node-removal resilience implementation
The Figure-3 network-fragmentation metric is implemented in `analysis/04_string_network.py` and fully specified in `docs/NODE_REMOVAL_RESILIENCE.md`. Primary normalization is LCC/original node count, AUC interval is removed-node fraction 0–0.5, random removal uses 100 fixed-seed replicates by default, and degree/betweenness targets are recomputed adaptively after each deletion.
