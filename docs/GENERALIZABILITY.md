# Dataset adapter and transfer boundary

The orchestration layer is designed to be reusable across molecular cohorts, but repository-specific input files require explicit adapters.

A new cohort should expose:
1. an expression matrix;
2. a clinical table with stable sample/patient identifiers and variables required by the requested goal;
3. a gene/sample identifier mapping specification.

The adapter is responsible for format ingestion, orientation detection, column normalization, missing-value parsing, identifier standardization and sample linkage. The controller remains responsible for registered analysis actions, verification, provenance, safety, escalation and stopping.

## Prespecified TCGA-BLCA adapter

`adapters/tcga_blca_adapter.py` implements the schema-harmonization contract for the future held-out TCGA-BLCA transfer test. It does **not** claim that empirical cross-disease transfer has already been demonstrated.

The adapter now performs the operations stated in the manuscript rather than assuming that they were completed manually beforehand:

- reads CSV/TSV expression and clinical tables;
- resolves clinical identifier columns after deterministic snake-case normalization;
- detects gene-by-sample versus sample-by-gene expression orientation from clinical-identifier overlap;
- recognizes common explicit missing-value tokens;
- standardizes gene symbols or Ensembl identifiers (including removal of Ensembl version suffixes);
- optionally applies an explicit Ensembl-to-symbol mapping table;
- aligns expression and clinical records by exact stable ID or, for TCGA barcodes, by the deterministic participant identifier (`TCGA-XX-YYYY`);
- collapses duplicate standardized gene identifiers by the median expression value;
- writes a machine-readable adapter audit describing every resolved choice.

No disease-specific controller action, benchmark threshold, terminal rule, action cost or reference-policy rule is modified by this adapter.

### Fail-safe boundary

If orientation, required identifier columns, identifier mapping or sample linkage cannot be resolved unambiguously, the adapter does not guess. It writes `adapter_audit.json` and `adapter_report.csv` with `status = HUMAN_REVIEW`, records the unresolved condition, and exits non-zero before writing a canonical adapted expression/clinical pair.

This implements the manuscript's stated boundary that unresolved format/schema questions should become an explicit human-review condition rather than hidden manual preprocessing.

### Example

For a gene-by-sample matrix with gene symbols and a clinical table containing one recognizable stable sample identifier:

```bash
python adapters/tcga_blca_adapter.py \
  --expression /path/to/blca_expression.csv \
  --clinical /path/to/blca_clinical.csv \
  --outdir /tmp/adapted_blca
```

For sample-by-gene Ensembl expression requiring explicit mapping:

```bash
python adapters/tcga_blca_adapter.py \
  --expression /path/to/blca_expression.csv \
  --clinical /path/to/blca_clinical.csv \
  --expression-sample-col "participant barcode" \
  --gene-namespace ensembl \
  --gene-mapping /path/to/ensembl_to_symbol.tsv \
  --mapping-source-col ensembl_id \
  --mapping-target-col gene_symbol \
  --outdir /tmp/adapted_blca
```

Successful execution writes:

- `expression_common_schema.csv` — canonical gene-by-sample matrix;
- `clinical_common_schema.csv` — aligned normalized clinical table;
- `adapter_audit.json` — detailed machine-readable harmonization audit;
- `adapter_report.csv` — one-row audit summary.

The held-out BLCA molecular execution remains future work. These adapter capabilities make that prespecified test executable without turning an unperformed transfer experiment into a reported result.
