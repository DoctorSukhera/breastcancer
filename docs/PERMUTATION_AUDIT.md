# Age-label permutation design audit

The manuscript primary permutation test is an **ER-stratified age-label null**. Age labels are permuted independently within ER-positive, ER-negative and explicit `Unknown` ER strata. The `Unknown` stratum is retained rather than discarded or merged with a biological receptor category.

The released implementation is `analysis/06_permutation_bootstrap.py`. Its default is therefore:

```bash
--strata ER
```

Alternative comma-separated strata (for example `--strata ER,PR`) remain available only as explicit sensitivity-analysis overrides; they are not the manuscript primary design.

Every run writes a JSON audit summary alongside the permutation-count CSV. The summary records the stratification columns, matched sample count, number and sizes of strata, random seed, number of permutations, observed FDR-significant gene count and add-one empirical P value.

## Provenance boundary

The earlier project analysis notebook that generated the reported workflow also used ER-only stratification and mapped missing ER values to `Unknown`. The previous repository default of `ER,PR,HER2,stage` was therefore a release-script mismatch, not the design used in that analysis or described in the manuscript.

Patient-level TCGA expression/clinical inputs are not redistributed in this repository. Consequently the release package can verify the implementation and design alignment, but it does not claim a fresh molecular rerun of the reported `126` observed genes or empirical `P = 0.001996` without the external source files.
