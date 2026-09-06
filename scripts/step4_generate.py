"""
STEP 4 — full generation, run LOCALLY.

Answers all 490 golden questions with the production remote stack (OpenRouter
for the LLM, Voyage for embeddings + rerank) and writes
evaluation/reports/pipeline_results.json. Runs NO judges: scoring happens in
step 5 on the pod, where ollama/qwen3 lives.

    python -m scripts.step4_generate

Then package the results for the pod:

    bash scripts/package_for_pod.sh
"""
import time

from evaluation.harness import run_evaluation
import settings as config

# All 490 questions. Set to a small int for a smoke run.
QUESTION_LIMIT = None

def main() -> None:
    t0 = time.time()
    res = run_evaluation(
        candidates=None,
        components=None,          # irrelevant while dry_run=True
        category_filter=None,
        top_k=config.RETRIEVE_TOP_K,
        judge_model="qwen3",      # unused here; step 5 does the judging
        dry_run=True,             # generation only — no judges, no report
        reuse_results=False,      # actually run the agent
        # Per-candidate checkpoints are written to reports/partial/ regardless;
        # resuming from them is what stops a network blip mid-run from re-paying
        # for every question already answered.
        resume=True,
        question_limit=QUESTION_LIMIT,
        # Keep the ChromaDB collections a previous run built. They are
        # deterministic for unchanged documents, and re-ingesting would re-pay
        # every per-document summary call. Flip to False if the documents, the
        # chunker, or EMBED_PROVIDER changed since they were built.
        reuse_ingestion=True,
    )

    n = len(res.get("pipeline_results") or [])
    wall = time.time() - t0
    print("\n" + "=" * 66)
    print(f"STEP 4 COMPLETE — {n} questions in {wall/60:.1f} min ({wall/max(n,1):.1f}s each)")
    print("=" * 66)
    print("  wrote evaluation/reports/pipeline_results.json")
    print("\nNext:  bash scripts/package_for_pod.sh")


# Guarded: without this, merely IMPORTING this module starts a full paid
# generation run — which is what happens during test collection, linting, or an
# IDE's auto-import. The work must only happen on an explicit invocation.
if __name__ == "__main__":
    main()
