from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "generate_figures_2_6.py"


def test_figure5_6_have_no_embedded_benchmark_dataframe_literals():
    text = SCRIPT.read_text(encoding="utf-8")
    forbidden = [
        "FIG5_COMPOSITION = pd.DataFrame(",
        "FIG5_CONTROLLERS = pd.DataFrame(",
        "FIG5_PAIRED = pd.DataFrame(",
        "FIG5_TRACES = pd.DataFrame(",
        "FIG6 = pd.DataFrame(",
        "FIG6_FAILURE_SIGNATURES = pd.DataFrame(",
        "Revision v0.13 authoritative benchmark values",
    ]
    for token in forbidden:
        assert token not in text, f"historical benchmark literal remains in plotting code: {token}"


def test_known_obsolete_benchmark_literals_are_absent_from_plotting_code():
    text = SCRIPT.read_text(encoding="utf-8")
    obsolete = [
        "0.075000", "0.702632", "0.781579", "0.987993", "4.475592",
        "7.648841", "1.85e-68", "1.07e-50", "9.61e-145", "1.65e-83", "9.50e-66",
        "0.988 → 0.883", "1.000 → 0.845",
        "Reference outcomes: 629 COMPLETE, 60 BLOCK, 71 FAIL_SAFE",
        "Same 760 scenarios and reference policy",
    ]
    for token in obsolete:
        assert token not in text, f"obsolete benchmark value remains in plotting code: {token}"


def test_figure5_6_are_loaded_from_source_tables_and_validate_structurally():
    text = SCRIPT.read_text(encoding="utf-8")
    required_loads = [
        'FIG5_COMPOSITION = pd.read_csv(SOURCE_DIR / "Figure5_scenario_composition.csv")',
        'FIG5_CONTROLLERS = pd.read_csv(SOURCE_DIR / "Figure5_controller_summary.csv")',
        'FIG5_PAIRED = pd.read_csv(SOURCE_DIR / "Figure5_paired_policy_comparisons.csv")',
        'FIG5_TRACES = pd.read_csv(SOURCE_DIR / "Figure5_representative_traces.csv")',
        'FIG6 = pd.read_csv(SOURCE_DIR / "Figure6_ablation_summary.csv")',
        'FIG6_FAILURE_SIGNATURES = pd.read_csv(SOURCE_DIR / "Figure6_failure_signatures.csv")',
    ]
    for token in required_loads:
        assert token in text

    spec = importlib.util.spec_from_file_location("figure_module_issue21", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    module.validate_source_tables()
