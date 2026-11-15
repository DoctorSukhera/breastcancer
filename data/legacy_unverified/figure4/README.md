# Legacy Figure 4 module-level artifacts — not active evidence

These two files are retained **only for audit provenance**:

- `Figure4_representative_modules_UNVERIFIED.csv`
- `Figure4_candidate_module_matrix_UNVERIFIED.csv`

They were present in earlier repository checkpoints as plotting inputs, but the
historical full GO/KEGG enrichment output and exact 180-term clustering record
needed to independently verify every module identity, module size, adjusted
P-value, and candidate×module membership cell are not bundled with the release.

For that reason:

1. these files are excluded from `data/source_tables/`;
2. no publication figure reads them;
3. no module-level row or matrix cell should be cited as independently reproduced
   evidence from this release; and
4. a legitimate future molecular rerun must regenerate module-level results from
   frozen GO/KEGG gene-set snapshots using the executable enrichment pipeline.

The active Figure 4 uses only `data/source_tables/Figure4_enrichment_counts.csv`,
which contains the archived aggregate quantities: tested terms, BH-FDR-significant
terms, top terms entered into redundancy reduction, representative-component
count, and Jaccard threshold.
