# Node-removal resilience protocol

The network-fragmentation sensitivity analysis is evaluated on the **STRING required-score 700 graph**.

## Curve definition

Let the original graph contain `N0` mapped nodes. After `k` deletions:

- `x_k = k / N0` is the fraction of original nodes removed.
- `y_k = LCC_k / N0` is the number of nodes in the largest connected component divided by the **original** node count.

Thus the ordinate is not normalized by the number of nodes remaining. The primary resilience summary is the trapezoidal area under `y(x)` over **x = 0 to 0.5**. For odd `N0`, the last segment is linearly interpolated so every strategy is integrated to exactly 0.5.

A lower AUC means that the largest connected component collapses faster over the first half of node deletions. It is a graph-fragmentation metric, not evidence of biological essentiality, druggability, or therapeutic vulnerability.

## Removal strategies

- **Random:** 100 independent replicates by default, integer seeds 0–99. At each step one node is sampled uniformly from the lexicographically sorted list of remaining nodes. The reported AUC is the mean across replicates; replicate-level AUCs and complete curves are exported.
- **Degree-targeted:** adaptive attack. Degree is recomputed after every deletion. Exact ties are resolved lexicographically.
- **Betweenness-targeted:** adaptive attack. NetworkX betweenness centrality is recomputed after every deletion. Exact ties are resolved lexicographically.

The defaults can be changed with `--random-replicates`, `--random-seed-start`, and `--attack-max-fraction`, but changing them constitutes a sensitivity analysis rather than the manuscript-primary protocol.

## Outputs

`analysis/04_string_network.py` writes:

- `node_removal_resilience.csv` — strategy-level mean AUC and protocol fields.
- `node_removal_resilience_replicates.csv` — every random-replicate AUC plus deterministic targeted AUCs.
- `node_removal_resilience_curves.csv` — all `(fraction_removed, LCC/original-N)` curve points.
- `node_removal_protocol.json` — machine-readable protocol metadata.

## Historical-result boundary

The manuscript reports archived AUC values of 0.283 (random), 0.146 (degree-targeted), and 0.155 (betweenness-targeted). Historical figure provenance specifies `LCC/original N` and AUC over 0–0.5, matching the corrected implementation. The exact historical score-700 edge list is not bundled in the release, so those three manuscript values are retained as archived source-table results rather than being falsely presented as freshly recomputed values. A legitimate molecular rerun with the required STRING edge/mapping inputs will generate new protocol-complete resilience outputs automatically.
