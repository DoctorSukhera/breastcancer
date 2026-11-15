# Figure reproducibility status — revised submission

| Manuscript figure | Files included | Script-level reproduction status |
|---|---|---|
| Figure 1 | Submitted composite; original repository-native figure; vector parts when retained | **Not yet reconciled** with exact submitted composite |
| Figure 2 | Corrected source-table-based four-panel figure, original source CSV and script | Corrected plot panels and combined PNG reproducible using `scripts/final_figure_panels/regenerate_figure2.py`; does not rerun patient-level models |
| Figure 3 | Submitted composite; repository-native figure; standalone vectors when retained | **Not yet reconciled** with exact submitted composite |
| Figure 4 | Submitted composite; legacy repository-native figure | **Not yet reconciled**; historical enrichment input genes, background, libraries and 30-module identities are not fully archived |
| Figure 5 | Corrected 5-controller source-driven figure and script | Regenerates using `results/generated` files; the complete benchmark can be rerun independently |
| Figure 6 | Submitted four-panel composite; repository-native figure; source tables | **Not yet reconciled** with exact submitted composite; repository generator produces an alternative figure |

`figures/Figure_1.png` through `Figure_6.png` (and corresponding SVG/PDF) are the *original repository-generated figures*, **not the revised submission artwork**. The revised submission files are under `figures/submitted_composites/`. Do not represent the repository-native generator as reproducing all six revised composites.

The original source-table graphics are not patient-level reproductions of TCGA-BRCA or GSE42568. The latter analyses require externally retrieved, correctly preprocessed source datasets.

The corrected Figure 2 panels were regenerated from archived candidate statistics with signed coefficients and FDR checks. The corrected Figure 5 includes the deterministic error-handling comparator and distinguishes policy conformance from action appropriateness.

Before journal submission: (1) independently verify exact Figure 2 and Figure 5 exports against submitted images, (2) reconcile plotting/assembly scripts for Figures 1, 3, 4 and 6, (3) resolve historical enrichment provenance, and (4) update response letter claims accordingly.

## Packaging smoke tests

- Corrected Figure 2 script: executed successfully from the repository-relative path; automated per-gene checks passed.
- Corrected Figure 5 script: source paths were made repository-relative; its *full fresh run did not finish within the available execution window during this packaging step*. Previously archived Figure 5 outputs are included; do not report this packaging attempt as a successful rerun.
- Manifest is regenerated after packaging to include the corrected Figure 2 SVG exports.
