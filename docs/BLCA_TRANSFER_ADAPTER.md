# TCGA-BLCA held-out transfer adapter

This document specifies the **schema-adaptation layer only** for the prespecified future TCGA-BLCA transfer experiment. It is not evidence of completed cross-disease generalization.

## Common input contract

The adapter converts either gene-by-sample or sample-by-gene expression tables into a canonical gene-by-sample matrix and aligns it to a normalized clinical table. The user supplies the source files and, where needed, explicit identifier/mapping choices. The adapter performs format/schema harmonization; the controller and molecular-analysis scripts perform the scientific workflow.

## Deterministic responsibilities

1. **Format ingestion** — CSV/TSV delimiter handling.
2. **Column normalization** — clinical headers are converted deterministically to snake case.
3. **Orientation detection** — orientation is selected from clinical-ID overlap. If both orientations are equally plausible, execution stops for human review.
4. **Missing-value parsing** — common explicit missing tokens are converted to missing values rather than treated as biological categories or identifiers.
5. **Gene-ID standardization** — gene symbols are uppercased; Ensembl version suffixes are stripped. An optional explicit mapping file can convert Ensembl IDs to symbols.
6. **Sample linkage** — exact stable-ID linkage is preferred. If no exact overlap exists and all IDs are valid TCGA barcodes, the adapter can link by the deterministic participant barcode prefix. Many-to-one linkage is rejected as ambiguous.
7. **Audit** — every successful or failed adaptation writes a machine-readable audit.

## Human-review conditions

The adapter returns `status = HUMAN_REVIEW` and exits non-zero for conditions including:

- no identifiable clinical sample/patient ID column;
- multiple equally plausible clinical ID columns;
- unresolved or tied expression orientation;
- no expression/clinical overlap;
- duplicate clinical IDs;
- many-to-one sample linkage;
- ambiguous gene mappings.

No controller or evaluator thresholds are changed in response to BLCA data.
