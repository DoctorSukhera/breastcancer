# Reproducibility guide

## What can be reproduced without external molecular data?

The complete 760-scenario controller benchmark, deterministic comparator, component ablations, statistical comparisons, and Figures 1–6 can be regenerated from files included in this repository.

Run:

```bash
python run_all.py
```

This command first validates the shipped frozen benchmark against `data/frozen/FREEZE_MANIFEST.json`, then executes controllers and ablations, regenerates finite-benchmark paired-effect and family-sensitivity tables, runs invariants/tests, and regenerates Figures 1–6 from frozen source tables. It validates the frozen benchmark again at the end. The released workflow does **not** rebuild or rewrite `data/frozen/`.

## Frozen-input immutability

`data/frozen/` is release input, not a runtime workspace. `run_all.py` validates it before execution and again after all benchmark/test/figure steps. `benchmark/build_frozen_inputs.py` is a developer-only release-generation utility and refuses to rewrite the frozen benchmark unless the explicit `--confirm-rebuild` flag is supplied. A benchmark rebuild therefore represents creation of a new benchmark release, not ordinary reproduction of the current one.

Developer-only regeneration command:

```bash
python benchmark/build_frozen_inputs.py --confirm-rebuild
```

After intentional regeneration, the resulting benchmark files and `FREEZE_MANIFEST.json` must be reviewed and versioned as a new frozen release before distribution.

## Molecular analysis

The molecular-analysis scripts are released, but public source files from TCGA/GDC, GEO, STRING, GO and KEGG are not redistributed here. See `docs/DATA_SOURCES.md` for expected inputs and example invocations. In the TCGA adjusted model, missing ER/PR/HER2/stage entries are encoded as the explicit `Unknown` category before modeling; only missing expression or age removes a subject from a gene-specific adjusted fit. Because patient-level TCGA inputs are not shipped in the repository, `run_all.py` does not claim to recompute the molecular headline counts without those external inputs. The primary age-label permutation design is ER-stratified (ER-positive, ER-negative and explicit `Unknown` ER strata); `analysis/06_permutation_bootstrap.py` defaults to `--strata ER` and writes a JSON audit summary documenting the strata used.


## Prespecified TCGA-BLCA adapter

The future held-out BLCA transfer protocol uses `adapters/tcga_blca_adapter.py` as an explicit schema boundary. The adapter supports gene-by-sample and sample-by-gene orientation detection, clinical-header normalization, missing-value parsing, symbol/Ensembl identifier standardization with optional explicit mapping, and exact or TCGA participant-level sample linkage. Ambiguous orientation, identifiers or linkage produce a `HUMAN_REVIEW` audit rather than a guessed mapping. This makes the adapter behavior executable while preserving the manuscript boundary that no completed BLCA transfer result is claimed. See `docs/BLCA_TRANSFER_ADAPTER.md`.

## Numerical source data for figures

`data/source_tables/` contains the numerical source tables used by the current manuscript figures. `scripts/generate_figures_2_6.py` reads these files and does not overwrite them. `scripts/generate_figure1.py` generates the conceptual workflow figure.

## Integrity

`SHA256_MANIFEST.csv` records byte-level SHA-256 hashes for the complete release tree, excluding only the manifest itself and transient cache files. It is generated deterministically with `python scripts/repository_manifest.py --write` during release authoring and validated with `python scripts/repository_manifest.py --validate`. Figure PDF/SVG generation uses fixed metadata and a fixed SVG hash salt so unchanged scientific figures reproduce byte-identically rather than changing only because of timestamps or randomized internal IDs. `benchmark/validate_package.py` and `tests/test_invariants.py` separately check the benchmark/reference split and manuscript-reported invariants.

## Sequence-aware action relevance

`benchmark/evaluator.py` evaluates action appropriateness from the ordered attempted trajectory rather than set membership. Each trajectory is compared with the independently generated scenario-specific oracle trace. Exact traces and non-empty valid prefixes are appropriate; wrong order, unnecessary/duplicate actions, wrong recovery routes, missing mandatory governance steps, unregistered actions and prerequisite violations are rejected. Diagnostic columns identifying the expected trace and first mismatch are written to trajectory-level outputs.

## Architectural ablations

`benchmark/ablation_controller.py` defines executable module-disabled controller variants. `benchmark/run_ablation.py` reruns all 760 scenarios independently for each variant. No full-controller trajectory is copied, deep-copied, or post-hoc edited to manufacture an ablation result. The full configuration is regression-tested to be behaviorally identical to the ordinary bounded controller.

## Strong deterministic comparator

The conventional deterministic error-handling comparator is goal-specific. It executes the requested canonical/held-out workflow, preflights known source outages to the registered cache, uses a fixed retry-once rule for runtime transient failure, applies the same hard safety/evidence fail-safe boundaries, and repairs corrupted provenance before reporting. It does not perform cost-aware source optimization and does not use the bounded controller's mode-specific retry-vs-fallback policy. It is therefore a strong conventional comparator rather than a deliberately over-executing full-workflow baseline.


## Statistical interpretation boundary

The 760 scenarios are a complete constructed benchmark, not an iid sample from an external task population. Generated comparison tables therefore contain exact paired benchmark effects, win/tie/loss counts, family-level effects and leave-one-family-out sensitivity ranges. They intentionally do not contain population-level P values or bootstrap confidence intervals.

### Full external-data molecular rerun

The release now provides a config-driven orchestrator at
`analysis/run_molecular_pipeline.py`. A template is supplied at
`docs/molecular_config.example.json`. The orchestrator validates every required
external path and schema before execution, runs the molecular scripts in
analysis order, and writes `MOLECULAR_RUN_MANIFEST.json` with the input paths,
settings, and derived outputs.

`python run_all.py` continues to be fully executable from the release alone, but
it explicitly reports `MOLECULAR REPRODUCTION STATUS: EXTERNAL INPUTS REQUIRED`
rather than implying that TCGA/GEO/STRING/GO-KEGG analyses were recomputed.
Supplying `--molecular-config` activates the full molecular rerun. Its configured
output directory must be outside the immutable release repository.

## Complete molecular result-table package

A successful config-driven molecular run executes `analysis/08_compile_molecular_tables.py` after all analysis stages and creates `<output_dir>/08_complete_tables/`. This is the reviewer-auditable derived-result layer behind compact figure/source summaries. It includes all curated-gene TCGA statistics, every locked candidate across downstream evidence layers, all-threshold STRING node/edge outputs, all computed enrichment rows plus clustering membership, the full permutation null distribution, and a SHA-256 table inventory. No subject-level TCGA/GEO records are copied into these exports. See `docs/MOLECULAR_RESULT_TABLES.md`.

### Reproducible GO/KEGG enrichment

The molecular runner no longer requires a precomputed enrichment table. It requires frozen local GO Biological Process and KEGG Human gene-set snapshots and computes over-representation statistics itself (`analysis/05_enrichment_analysis.py`). This avoids dependence on mutable live Enrichr library discovery. The exact snapshot names and SHA-256 hashes are recorded in the enrichment audit JSON before redundancy reduction.

## Figure 5/6 single-source benchmark values

`scripts/generate_figures_2_6.py` does not contain fallback benchmark or ablation results. Figure-5 composition, controller summaries, paired finite-benchmark effects, representative traces, Figure-6 ablation summaries, and failure signatures are read from `data/source_tables/`. The script performs structural schema validation only; it does not assert expected scientific results by embedding numeric constants in Python source. `tests/test_issue21_no_historical_plot_constants.py` guards this invariant.

## Figure 5 controller-summary synchronization

`data/source_tables/Figure5_controller_summary.csv` is not an independent numerical result. It is a compact plotting projection of `results/generated/benchmark_controller_summary.csv`. After `benchmark/analyze_results.py`, `scripts/sync_figure5_controller_summary.py` deterministically maps the authoritative controller metrics into the Figure-5 schema before figure generation. `tests/test_issue22_figure5_source_sync.py` enforces numerical equality and prevents the plotting copy from drifting from the benchmark results again.

## Network-resilience reproducibility
`analysis/04_string_network.py` now emits `node_removal_protocol.json`, `node_removal_resilience_curves.csv`, replicate-level AUCs, and strategy summaries. The primary protocol uses the score-700 graph, normalizes LCC size by the original node count, integrates AUC over node-removal fraction 0–0.5, uses 100 random replicates with seeds 0–99, and recomputes degree/betweenness adaptively after each targeted deletion. See `docs/NODE_REMOVAL_RESILIENCE.md`.

## Figure 4 module-level evidence boundary

The release can reproduce the aggregate Figure 4 enrichment counts from
`data/source_tables/Figure4_enrichment_counts.csv`, but it cannot independently
reconstruct the historical exact 30-module identities or the candidate×module
membership matrix because the original full enrichment output and 180-term
clustering record are not bundled. `scripts/generate_figures_2_6.py` therefore
uses only the aggregate count table for Figure 4. Historical module-level CSVs are
quarantined under `data/legacy_unverified/figure4/` and are explicitly excluded
from the active plotting path. A future molecular rerun may regenerate module-level
outputs from frozen GO/KEGG gene-set snapshots using the executable enrichment
pipeline introduced in Issue 19.
