# Normalized action-cost model

The benchmark's `normalized_cost` values are **abstract workflow-resource units**, not measured wall-clock seconds, monetary costs, GPU-hours or clinical utility weights. They are frozen in `data/frozen/action_registry.csv` and applied identically to every controller.

The cost model exists to test whether a controller can avoid unnecessary registered actions and select the lower-cost valid route when the benchmark explicitly presents alternatives. Absolute cost magnitudes should therefore not be interpreted outside this finite benchmark.

Two safeguards limit dependence on the particular weights:

1. **Mean action count is reported separately from normalized cost.** At the current integrity checkpoint, the bounded controller and the strong deterministic comparator both use 7.028 actions per scenario on average. Their remaining resource difference therefore comes from route choice (e.g., cost-aware cache selection and mode-specific transient recovery), not from forcing the deterministic comparator to execute a longer workflow.
2. **Resource stewardship uses the same frozen registry for observed and oracle trajectories.** Forced perturbation costs (for example a benchmark-injected failed attempt) are included in the oracle when appropriate, so the controller is not penalized for costs imposed by the scenario definition.

A future external benchmark should recalibrate action costs to measured compute/time/resource use before interpreting stewardship quantitatively across systems or hardware.
