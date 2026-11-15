from pathlib import Path
import importlib.util
import pandas as pd
import pandas.testing as pdt

ROOT = Path(__file__).resolve().parents[1]
SYNC = ROOT / "scripts" / "sync_figure5_controller_summary.py"
TARGET = ROOT / "data" / "source_tables" / "Figure5_controller_summary.csv"
GENERATED = ROOT / "results" / "generated" / "benchmark_controller_summary.csv"


def _module():
    spec = importlib.util.spec_from_file_location("issue22_sync", SYNC)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_figure5_controller_table_is_exact_projection_of_generated_benchmark_summary():
    module = _module()
    expected = module.projected_table(GENERATED)
    observed = pd.read_csv(TARGET)
    pdt.assert_frame_equal(observed, expected, check_exact=False, rtol=1e-12, atol=1e-12)


def test_figure5_controller_table_has_no_missing_process_metrics():
    df = pd.read_csv(TARGET)
    required = ["policy", "action", "safety", "provenance", "escalation", "stewardship", "mean_cost"]
    assert not df[required].isna().any().any()
    assert df["system"].tolist() == [
        "Static workflow", "Goal planner", "Adaptive planner", "Bounded controller"
    ]


def test_run_all_synchronizes_figure5_after_benchmark_analysis():
    text = (ROOT / "run_all.py").read_text(encoding="utf-8")
    analyze = text.index("benchmark/analyze_results.py")
    sync = text.index("scripts/sync_figure5_controller_summary.py")
    figures = text.index("scripts/generate_figures_2_6.py")
    assert analyze < sync < figures
