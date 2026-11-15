# Public data sources and expected local files

The repository does **not** redistribute controlled or patient-level TCGA files. Users should obtain public source data from the original repositories and pass local paths to the analysis scripts.

## GenAge/HAGR
Human ageing-related genes are obtained from the Human Ageing Genomic Resources (HAGR) GenAge human-gene dataset.

- Landing page: https://hagr.ageing-map.org/genes/
- Human-gene page/download: https://hagr.ageing-map.org/genes/human.html

The discovery analysis used the curated human ageing-gene list (307 genes in the manuscript analysis). Save a one-column gene-symbol file and pass it to `analysis/01_tcga_age_association.py --genage`.

## TCGA-BRCA
The discovery cohort is TCGA Breast Invasive Carcinoma (TCGA-BRCA) from the NCI Genomic Data Commons.

- Portal: https://portal.gdc.cancer.gov/

The manuscript analysis uses primary tumors, a gene-expression matrix already represented as `log2(UQ-FPKM + 1)`, and clinical covariates including age, ER, PR, HER2 and pathological stage. The repository does not convert normalized FPKM values into pseudo-counts and does not apply DESeq2 to this matrix.

Expected local inputs:
- gene x sample expression CSV/TSV;
- clinical CSV/TSV with stable sample IDs and required covariates.

### TCGA clinical missing-data rule
For the primary covariate-adjusted model, missing/unavailable ER, PR, HER2 and pathological-stage values are retained as the explicit categorical level `Unknown`; they are **not** complete-case deleted and are not merged into a biological reference category. `analysis/01_tcga_age_association.py` normalizes common missing-value tokens (for example blank/NA/not available/not reported) to this level before fitting the HC3-robust OLS model. The script writes `tcga_covariate_missingness_summary.csv` so the number of subjects assigned to the explicit missing category is auditable for each covariate. Rows are removed from a gene-specific adjusted fit only when the expression outcome or age term is unavailable.

## GSE42568
Independent expression replication uses NCBI GEO series GSE42568.

- Series URL: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE42568

The replication script expects a processed probe x sample matrix, a platform annotation table mapping probes to gene symbols, and sample metadata containing age. Multiple probes mapping to one symbol are collapsed by the median in the released script.

## STRING
Protein-association analysis uses STRING human protein associations. STRING combined confidence scores in downloadable files are multiplied by 1000.

- Download page: https://string-db.org/cgi/download

The manuscript reports thresholds 400, 700 and 900 and uses score 700 as the primary high-confidence network. A STRING edge is treated as an evidence-supported functional/physical association, not necessarily direct binding or binding strength.

## GO and KEGG enrichment

The historical analysis used GSEApy/Enrichr with a GO Biological Process library and a KEGG Human library. Live Enrichr library discovery is not used by the released primary reproduction path because library names and contents can change over time.

A reproducible molecular rerun therefore requires explicit local gene-set snapshots:

- `go_gene_sets`: GO Biological Process GMT (or a table with `term` and `genes` columns);
- `kegg_gene_sets`: KEGG Human GMT (or a table with `term` and `genes` columns);
- optional `enrichment_background`: explicit background gene list. If omitted, each source library's gene-set union is used as its statistical universe.

`analysis/05_enrichment_analysis.py` computes one-sided hypergeometric over-representation P values and applies Benjamini-Hochberg correction within each source library. It records the exact library labels and SHA-256 hashes in `enrichment_analysis_audit.json`. The generated `enrichment_computed.csv` is then passed to `analysis/05_enrichment_redundancy.py`, which performs the manuscript's FDR filtering and Jaccard-based redundancy reduction.

The manuscript reports 1,698 tested terms, 514 BH-FDR-significant terms, the 180 most significant terms used for overlap clustering, and 30 representative modules at gene-set Jaccard threshold 0.40. Those historical counts are not regenerated unless the exact historical gene-set snapshots are supplied.

## Held-out transfer protocol
`adapters/tcga_blca_adapter.py` implements the schema-harmonization step for the prespecified TCGA-BLCA transfer protocol: format ingestion, orientation detection, normalized clinical headers, missing-value parsing, gene-identifier standardization/optional mapping, exact or deterministic TCGA participant linkage, and explicit HUMAN_REVIEW output when a required mapping is ambiguous. It does not alter controller rules, thresholds or benchmark scoring. See `docs/BLCA_TRANSFER_ADAPTER.md`.

## One-command molecular rerun

After downloading and harmonizing the external source files above, copy
`docs/molecular_config.example.json`, replace the placeholder paths, and run:

```bash
python analysis/run_molecular_pipeline.py --config /path/to/molecular_config.json
```

The runner validates all paths and required table schemas **before starting any
analysis**, executes the released molecular scripts in dependency order, creates
the adjusted-FDR-significant gene list consumed by the ER/STRING stages, and
writes `MOLECULAR_RUN_MANIFEST.json` containing the exact external input paths,
settings and derived-output locations.

To include this rerun in the repository-level reproducibility command, use:

```bash
python run_all.py --molecular-config /path/to/molecular_config.json
```

For that mode, `output_dir` must be outside the release repository so that
external-data-derived outputs do not modify the immutable release SHA manifest.
Without `--molecular-config`, `run_all.py` reproduces the bundled benchmark and
figures and explicitly reports that the molecular analyses were not rerun.
