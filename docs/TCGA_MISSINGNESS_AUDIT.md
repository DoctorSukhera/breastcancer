# TCGA-BRCA covariate missingness rule

## Release rule
For the primary covariate-adjusted TCGA-BRCA model, unavailable values of ER, PR, HER2 and pathological stage are retained as the explicit categorical level `Unknown`.

They are not:

- complete-case deleted solely because a categorical clinicopathological value is unavailable; or
- merged into a biological reference category.

Gene-specific adjusted fits exclude a subject only when that gene's expression value or the age term is unavailable.

## Executable implementation
`analysis/01_tcga_age_association.py` applies `retain_missing_as_category()` before any adjusted model is constructed. Common placeholders such as blank values, NA/N/A, null, not available, not reported and not evaluated are normalized to the configured missing-category label (default `Unknown`).

Every rerun writes:

`tcga_covariate_missingness_summary.csv`

This file records, for ER, PR, HER2 and stage, how many matched subjects were assigned to the explicit missing category.

## Why this audit was added
An earlier release implementation used a `dropna()` call that included ER, PR, HER2 and stage, which was inconsistent with the manuscript's stated `Unknown`-category rule. The current release removes that inconsistency and regression-tests the behavior with a synthetic cohort containing multiple missing-value representations.

## Biological-result boundary
Patient-level TCGA expression/clinical inputs are not redistributed in this repository. Therefore the release-package integrity check can validate the preprocessing implementation but cannot independently recompute the manuscript's 80 adjusted FDR-significant genes without the external TCGA inputs. No molecular count, coefficient, candidate rank or figure source value is changed merely because the code path was corrected.
