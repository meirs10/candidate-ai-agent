"""
STEP 5 — full scoring, run ON THE POD.

Scores the answers step 4 generated locally, using the pod's GPU judges
(ollama/qwen3 for GEval + RAGAS + ingestion, local nomic embeddings for RAGAS).
Generation is NOT re-run: reuse_results=True reads pipeline_results.json.

Produces ALL SEVEN components, including `ingestion` and `retrieval_gates` —
which is why chroma_db has to be shipped over with the results (they read the
live collections, unlike the other five which only read pipeline_results.json).

Prerequisites on the pod (scripts/pod_setup.sh checks all of them):
  - evaluation/reports/pipeline_results.json   from step 4
  - chroma_db/                                 from step 4  <- easy to forget
  - ollama serving, with qwen3 pulled

    /workspace/venv/bin/python -m scripts.step5_score
"""
import time

from evaluation.harness import run_evaluation, ALL_COMPONENTS

t0 = time.time()
res = run_evaluation(
    candidates=None,
    components=ALL_COMPONENTS,   # all seven
    category_filter=None,
    top_k=8,
    judge_model="qwen3",
    dry_run=False,
    report_format="html",
    reuse_results=True,          # score step 4's answers; do not regenerate
    resume=False,
    question_limit=None,
    reuse_ingestion=True,        # use the shipped collections as-is
)

print("\n" + "=" * 66)
print(f"STEP 5 COMPLETE in {(time.time()-t0)/60:.1f} min")
print("=" * 66)
print("  report:", res.get("report_path"))

# Surface any component that silently produced nothing, so a missing section in
# the HTML is not mistaken for a zero score.
missing = [
    label for label, val in (
        ("tool_selection",  res.get("tool_eval_df")),
        ("rag (RAGAS)",     res.get("ragas_df")),
        ("retrieval_gates", res.get("gate_df")),
        ("geval",           res.get("geval_df")),
        ("refusal",         res.get("refusal_df")),
        ("ingestion",       res.get("ingestion_report")),
        ("router",          res.get("router_df")),
    ) if val is None
]
print(("  [WARN] produced no output: " + ", ".join(missing)) if missing
      else "  all 7 components produced output")
