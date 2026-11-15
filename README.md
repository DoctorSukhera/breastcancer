# Breast cancer molecular prioritization and bounded computational workflow governance

**Research code and data release — assembled 10 November 2026**

This is a GitHub-uploadable research archive, **not evidence that every external molecular analysis or submitted figure has been independently reproduced**. All methods and included outcomes should be interpreted within the limitations described in [`docs/DATA_AVAILABILITY_AND_LIMITATIONS.md`](docs/DATA_AVAILABILITY_AND_LIMITATIONS.md) and [`docs/FIGURE_REPRODUCIBILITY_STATUS.md`](docs/FIGURE_REPRODUCIBILITY_STATUS.md).

Useful starting points:
- `run_all.py`: constructed benchmark, comparators, ablations, internal tests and original repository-native figure generation.
- `figures/submitted_composites/`: six currently revised manuscript composite PNG files.
- `scripts/final_figure_panels/regenerate_figure2.py`: verified source-table-based Figure 2 panels.
- `scripts/final_figure_panels/regenerate_figure5.py`: five-controller Figure 5 panels from stored benchmark trajectories.
- `data/frozen/`: benchmark manifest, reference policy and immutable controller-visible inputs.
- `docs/GITHUB_UPLOAD_INSTRUCTIONS.md`: upload and versioning instructions.

---

# Reproducible Prioritization of Age-Associated Breast Cancer Genes with Bounded Computational Workflow Governance

This repository supports the revised research manuscript **“An Integrated In Silico Framework for Reproducible Prioritization of Age-Associated Genes in Breast Cancer.”**

It is organized to let reviewers inspect three layers separately:

1. **Molecular-analysis scripts** for age association, covariate adjustment, external replication, ER-stratified sensitivity, STRING network analysis, reproducible GO/KEGG over-representation analysis, enrichment redundancy reduction, permutation testing and candidate bootstrap analysis;
2. **A fully executable 760-scenario workflow-governance benchmark**, including the bounded controller, simple planning baselines, a strong conventional deterministic error-handling comparator, component ablations and trajectory-level evaluation;

   The deterministic comparator is goal-specific and uses conventional preflight fallback plus retry-once error handling; it is not forced to execute the full-prioritization workflow on every scenario.

   Component ablations are implemented as **fresh module-disabled controller executions**. Each variant starts from a new runtime state for every scenario; no ablation is produced by copying or editing the full controller's completed trajectory.
3. **Frozen numerical source tables and plotting scripts** for the repository-native Figures 1–6, plus the separately archived **corrected revised-submission figures**. The two sets are not identical; see `docs/FIGURE_REPRODUCIBILITY_STATUS.md`.

The repository does not claim that the controller autonomously generated the reported TCGA/GEO/STRING/GO-KEGG molecular findings. The molecular analysis and the controller benchmark are separately executed components linked by a common set of scientific workflow operations.

## Quick reproducibility check

Create an environment and install core dependencies:
Use Python 3.13 for the pinned environment. The archived validation used Python 3.13.5.

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Then run:

```bash
python run_all.py
```

The command validates the shipped frozen benchmark **before** execution, reruns all 760 scenarios, executes the deterministic comparator and ablations, regenerates finite-benchmark descriptive comparisons, runs invariant tests, regenerates Figures 1–6, and validates the frozen benchmark again. It does not rebuild or rewrite `data/frozen/`.

Expected headline outputs include:

- reference policy: **629 COMPLETE / 60 BLOCK / 71 FAIL_SAFE**;
- policy conformance: **0.368 / 0.558 / 0.716 / 1.000** for static / goal-planning / adaptive / bounded controllers (rounded);
- bounded controller: **1.000** feasible completion, action appropriateness, safety, provenance, escalation and resource stewardship;
- bounded mean normalized cost **4.829** and mean actions **7.028**;
- strong conventional deterministic comparator: terminal policy conformance **1.000**, sequence-aware action appropriateness **0.842**, resource stewardship **0.993**, mean normalized cost **4.868**, mean actions **7.028**;
- ablation policy conformance: replanning removed **0.921**, verifier removed **0.908**, safety gate removed **0.921**, provenance removed **0.934**, cost-awareness removed **1.000**.

See `REPRODUCIBILITY.md` for details.

## Repository layout

```text
analysis/                 public-data molecular analysis scripts
adapters/                 held-out dataset schema adapter
benchmark/                controller, evaluator, benchmark and statistics
llm/                      restricted LLM comparator protocol (no reported LLM results)
data/frozen/              reference-isolated 760-scenario benchmark files
data/source_tables/       frozen numerical source tables for Figures 2–6
docs/                     metric, scenario, data-source and scope documentation
figures/                  regenerated PNG/PDF/SVG Figures 1–6
results/generated/        outputs regenerated from benchmark code
results/reported/         manuscript-facing reported tables
scripts/                  figure-generation scripts
tests/                    invariant/reproducibility tests
```

## Molecular-analysis reproduction

Public molecular source files are not redistributed. See `docs/DATA_SOURCES.md` for sources and expected schemas. Example commands:

```bash
python analysis/01_tcga_age_association.py \
  --expression /path/to/tcga_brca_log2_uq_fpkm.csv \
  --clinical /path/to/tcga_brca_clinical.csv \
  --genage /path/to/genage_human_genes.txt

python analysis/02_external_replication.py \
  --series-matrix /path/to/GSE42568_expression.csv \
  --annotation /path/to/platform_annotation.csv \
  --metadata /path/to/GSE42568_metadata.csv \
  --locked results/molecular_tcga/locked_top40_candidates.csv
```

The released TCGA script uses normalized continuous `log2(UQ-FPKM+1)` values and HC3-robust OLS; it does **not** apply DESeq2 to normalized FPKM data. Missing ER, PR, HER2 and pathological-stage values are retained as an explicit `Unknown` category, matching the manuscript method, and the script writes a covariate-missingness audit table for every rerun. The global age-label permutation script likewise matches the manuscript design by permuting age within ER strata only by default, including an explicit `Unknown` ER stratum; alternative joint strata require an explicit `--strata` override.

Every full molecular rerun also generates `08_complete_tables/`, a standardized derived-result package containing complete gene-level TCGA statistics, the full locked-candidate multi-evidence table, all-threshold STRING node/edge tables, the full enrichment table and cluster membership, the complete permutation null distribution, and a SHA-256 inventory. See `docs/MOLECULAR_RESULT_TABLES.md`. Patient/sample-level source records are not exported into this package.

## Reference-policy isolation

`data/frozen/controller_input_manifest.csv` contains only the scientific goal and controller-observable perturbation state. Terminal outcomes and evaluation-only constraints are stored separately in `reference_policy.csv` and joined only after execution for scoring. `benchmark/validate_package.py` checks that evaluation-only fields do not leak into the controller manifest.

## Metrics

Formal executable definitions are documented in `docs/METRICS.md` and implemented in `benchmark/evaluator.py`. No manual relevance score is used for policy conformance, action appropriateness, safety, provenance, escalation or resource stewardship. Benchmark comparisons are treated as descriptive effects over the complete finite constructed test suite: the repository reports paired effect sizes, win/tie/loss counts, family-specific effects, and leave-one-family-out sensitivity ranges rather than population-level P values. Action appropriateness is sequence-aware: attempted scientific/governance actions must form an exact trace or non-empty valid prefix of the independently generated scenario-specific oracle trace, with no unregistered/prerequisite violation. The abstract normalized action-cost scheme and its interpretation limits are documented in `docs/COST_MODEL.md`.

## Figures

The original **repository-native** Figures 1–6 are generated programmatically by `scripts/generate_figure1.py` and `scripts/generate_figures_2_6.py`. The **revised submitted** figures are under `figures/submitted_composites/`. Corrected Figure 2 and Figure 5 panel scripts are under `scripts/final_figure_panels/`. **Exact revised composite reproduction is not yet verified for Figures 1, 3, 4 and 6.** See `docs/FIGURE_REPRODUCIBILITY_STATUS.md`.

## External LLM comparator

The manuscript does not report quantitative LLM-agent performance because no external LLM was executed and archived under the identical frozen inference environment. `llm/restricted_llm_protocol.py` is provided only as a transparent future-comparator protocol. See `docs/LLM_COMPARATOR.md`.

## Generalizability boundary

`adapters/tcga_blca_adapter.py` implements the prespecified schema-harmonization step for a future held-out TCGA-BLCA transfer test, including orientation detection, clinical-header normalization, missing-value parsing, gene-identifier standardization/mapping, deterministic sample linkage, and explicit HUMAN_REVIEW failure on unresolved schema/linkage conditions. The current manuscript does not claim completed empirical cross-disease transfer. See `docs/BLCA_TRANSFER_ADAPTER.md`.

## Data and licensing

The code in this repository retains the original MIT License; rights to externally sourced biological data and manuscript figures must be verified before reuse. Public biological resources remain subject to their original licenses/terms. Patient-level or controlled TCGA data are not redistributed.

## Integrity

`SHA256_MANIFEST.csv` records deterministic byte-level hashes for the release tree and can be checked with `python scripts/repository_manifest.py --validate`. Figure PDF/SVG metadata and SVG IDs are normalized so repeated figure regeneration is byte-stable. The frozen benchmark also has its own `data/frozen/FREEZE_MANIFEST.json`.
The benchmark builder is deliberately outside the normal reproduction path. To intentionally create a new frozen benchmark release, a developer must run `python benchmark/build_frozen_inputs.py --confirm-rebuild`; running the builder without that flag fails before writing any frozen file.


### Optional full molecular rerun from external source data

A single config-driven entry point is now available:

```bash
cp docs/molecular_config.example.json /tmp/molecular_config.json
# edit paths, then:
python analysis/run_molecular_pipeline.py --config /tmp/molecular_config.json
```

or combine it with the release workflow:

```bash
python run_all.py --molecular-config /tmp/molecular_config.json
```

The default `python run_all.py` does **not** imply that external TCGA/GEO/STRING/
GO-KEGG analyses were rerun; it reports that those inputs are required. This
separates bundled benchmark reproducibility from molecular reproduction that
requires user-obtained public source files.

## Figure benchmark single-source rendering

Figures 5 and 6 contain no embedded benchmark/controller/ablation result tables. `scripts/generate_figures_2_6.py` loads Figure-5/6 values exclusively from the corresponding CSV files in `data/source_tables/`, validates their schemas, and derives benchmark counts and ablation summary text from those loaded tables. Historical fallback constants and obsolete inferential P-value/CI blocks have been removed from plotting code.

## Figure 5 controller source-of-truth

The controller bars and bounded-controller metric panel in Figure 5 are synchronized from `results/generated/benchmark_controller_summary.csv` by `scripts/sync_figure5_controller_summary.py`. The compact `data/source_tables/Figure5_controller_summary.csv` is therefore a rendering projection, not a second independent result table. `run_all.py` performs the synchronization after benchmark analysis and before figure generation.

### Node-removal resilience protocol
The score-700 network resilience analysis is fully specified in `docs/NODE_REMOVAL_RESILIENCE.md`: LCC size is normalized to the original node count, AUC is integrated over removed-node fraction 0–0.5, random removal uses 100 fixed-seed replicates by default, and degree/betweenness attacks recompute centrality after every deletion. Full curves, replicate AUCs, and a machine-readable protocol audit are emitted by `analysis/04_string_network.py`.

## Issue 24: Figure 4 evidence boundary

Figure 4 now reports only archived aggregate enrichment quantities that can be
independently checked from the release: 1,698 tested terms, 514 BH-FDR-significant
terms (379 GO Biological Process and 135 KEGG), the top 180 terms entered into
Jaccard-based redundancy reduction, 30 representative overlap components, and the
Jaccard threshold of 0.40. The historical full enrichment table and exact 180-term
clustering output are not bundled, so exact representative-module identities,
module sizes, adjusted-P values, and candidate×module membership cells are not
presented as reproduced evidence. Earlier module-level plotting CSVs are retained
only under `data/legacy_unverified/figure4/` for audit provenance and are not read
by any publication figure.

### Citation integrity
A verified bibliography-correction registry is provided in `data/reference_corrections.csv`; explanatory provenance is in `docs/CITATION_AUDIT.md`. Issue 25 corrects the Liu et al. ALKBH5–FOXO1 Redox Biology record to article 102993, DOI 10.1016/j.redox.2023.102993.

### A2M evidence boundary
Issue 26 pins the pharmacological-contextualization wording for A2M to primary breast-cancer evidence. The release documents A2M as **Contextual / exploratory**, supported by published breast-cancer expression/survival and subtype-proteomics associations, but does not elevate those associations to established targetability or therapeutic efficacy. See `docs/A2M_EVIDENCE_AUDIT.md` and `data/pharmacology_evidence_audit.csv`.

### Issue 27 chronology clarification
The pharmacological contextualization/evidence-to-experiment triage is a **revision-added descriptive evidence layer**, introduced in response to peer review. It was not part of the original molecular analysis plan and must not be described as a prespecified validation endpoint. This chronology correction does not alter any molecular result, candidate class, pharmacological evidence category, or follow-up-route membership. See `docs/PHARMACOLOGY_CHRONOLOGY_AUDIT.md` and `data/pharmacology_chronology_audit.csv`.
