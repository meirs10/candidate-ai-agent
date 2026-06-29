"""
Rebuild the HTML evaluation report from the report files a run already wrote —
no pipeline run, no LLM judges, zero recompute.

Every scored run leaves these behind in evaluation/reports/ (regardless of the
chosen REPORT_FORMAT):
    pipeline_results.json        — every question + answer + contexts + metadata
    tool_selection_scores.csv    — tool-selection scores
    ragas_scores.csv             — RAGAS metrics (RAG-routed questions)
    retrieval_gate_scores.csv    — retrieval gate localization (if any)
    geval_scores.csv             — GEval answer-correctness
    refusal_scores.csv           — refusal confusion classes
    router_scores.csv            — broad/specific routing
    ingestion_report.json        — per-candidate ingestion quality
This reads those back and re-renders the HTML from them.

Standalone (without run_eval):
    python -m evaluation.regenerate_report                 # reads evaluation/reports/
    python -m evaluation.regenerate_report path/to/reports # a different reports dir

Programmatic (used by run_eval's REGENERATE_HTML_ONLY flag):
    from evaluation.regenerate_report import regenerate_html
    regenerate_html()
"""

import json
import sys
from pathlib import Path

import pandas as pd

from evaluation.report import REPORTS_DIR, generate_report

# Component CSV (as written by the harness) → the eval_results key the report
# builder consumes.
_CSV_TO_DF = {
    "tool_selection_scores.csv": "tool_eval_df",
    "ragas_scores.csv": "ragas_df",
    "retrieval_gate_scores.csv": "retrieval_gate_df",
    "geval_scores.csv": "geval_df",
    "refusal_scores.csv": "refusal_df",
    "router_scores.csv": "router_df",
}
_PIPELINE_FILE = "pipeline_results.json"
_INGESTION_FILE = "ingestion_report.json"


def _load_eval_results(reports_dir: Path) -> dict:
    """Reconstruct the eval_results dict from the per-component report files.

    Missing files (e.g. retrieval_gate_scores.csv when nothing was gated, or a
    component you didn't run) stay None, which the report renders as 'no data'.
    """
    eval_results: dict = {df_key: None for df_key in _CSV_TO_DF.values()}
    eval_results["ingestion_report"] = None

    for fname, df_key in _CSV_TO_DF.items():
        path = reports_dir / fname
        if path.exists():
            df = pd.read_csv(path)
            if len(df) > 0:
                eval_results[df_key] = df

    ingestion_path = reports_dir / _INGESTION_FILE
    if ingestion_path.exists():
        with open(ingestion_path, "r", encoding="utf-8") as f:
            eval_results["ingestion_report"] = json.load(f)

    return eval_results


def regenerate_html(reports_dir: str | Path | None = None) -> str:
    """Rebuild the HTML report from existing report files; return the new path."""
    reports_dir = Path(reports_dir) if reports_dir else REPORTS_DIR

    pipeline_path = reports_dir / _PIPELINE_FILE
    if not pipeline_path.exists():
        raise FileNotFoundError(
            f"{pipeline_path} not found — run the evaluation first "
            f"(python -m evaluation.run_eval), which writes the report files this "
            f"rebuilds from."
        )
    with open(pipeline_path, "r", encoding="utf-8") as f:
        pipeline_results = json.load(f)
    if not pipeline_results:
        raise ValueError(f"{pipeline_path} contains no results to report on.")

    eval_results = _load_eval_results(reports_dir)
    loaded = [k for k, v in eval_results.items() if v is not None]

    html_path = generate_report(pipeline_results, eval_results, output_format="html")
    print(f"[regenerate] Source: {reports_dir}")
    print(f"[regenerate] {len(pipeline_results)} questions, components: {loaded}")
    print(f"[regenerate] HTML rebuilt from existing reports (no recompute).")
    return html_path


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    out = regenerate_html(arg)
    print(f"\nHTML report regenerated: {out}")
