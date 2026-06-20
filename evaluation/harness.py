"""
Multi-candidate evaluation harness — orchestrates data seeding, pipeline
execution, component evaluations, and report generation across multiple
candidates, each with multiple documents.

Components:
  1. Tool Selection — expected vs actual tool
  2. RAG Quality — RAGAS (RAG-only)
  3. Answer Correctness — GEval (all questions)
  4. Refusal Accuracy — confusion matrix (all questions)
  5. Ingestion Quality — chunk stats, coverage, summary quality
  6. Router Accuracy — broad/specific classification
"""

import json
import os
import shutil
import time
from pathlib import Path

import chromadb
import pandas as pd

from evaluation.pipeline import (
    restore_candidate_id,
    run_full_pipeline,
    set_candidate_id,
)
from rag.ingest import ingest_document
from store.structured import DATA_PATH as STRUCTURED_DATA_PATH

# Paths
EVAL_DIR = Path(__file__).parent
DATA_DIR = EVAL_DIR / "data"
REPORTS_DIR = EVAL_DIR / "reports"
CHROMA_PATH = "./chroma_db"


# ── Discovery & helpers ─────────────────────────────────────────────────────


def _discover_candidates(candidates_filter: list[int] | None = None) -> list[dict]:
    """Scan data/ for candidate_* dirs.

    Returns list of:
        {"idx": 1, "dir": Path, "name": str, "eval_id": "eval_cand_1"}
    If candidates_filter is provided (e.g. [1, 4]), only those are returned.
    """
    candidates = []
    for d in sorted(DATA_DIR.iterdir()):
        if not d.is_dir() or not d.name.startswith("candidate_"):
            continue
        try:
            idx = int(d.name.split("_")[1])
        except (IndexError, ValueError):
            continue

        if candidates_filter and idx not in candidates_filter:
            continue

        # Read name from seed
        seed_path = d / "candidate_seed.json"
        if not seed_path.exists():
            continue
        with open(seed_path, encoding="utf-8") as f:
            seed = json.load(f)

        candidates.append(
            {
                "idx": idx,
                "dir": d,
                "name": seed.get("full_name", f"Candidate {idx}"),
                "eval_id": f"eval_cand_{idx}",
            }
        )

    return candidates


def _infer_doc_type(filename: str) -> str:
    """Infer doc_type from filename prefix."""
    lower = filename.lower()
    if lower.startswith("cv_"):
        return "cv"
    elif lower.startswith("readme_"):
        return "readme"
    elif lower.startswith("recommendation_"):
        return "recommendation"
    return "other"


def _get_doc_files(candidate_dir: Path) -> list[tuple[Path, str]]:
    """Return list of (file_path, doc_type) for all document files in the dir.

    Excludes candidate_seed.json and golden_dataset.json.
    """
    skip = {"candidate_seed.json", "golden_dataset.json"}
    doc_files = []
    for f in sorted(candidate_dir.iterdir()):
        if f.is_dir() or f.name in skip:
            continue
        doc_type = _infer_doc_type(f.name)
        doc_files.append((f, doc_type))
    return doc_files


# ── Seeding ──────────────────────────────────────────────────────────────────


def _load_golden_dataset(
    candidate_dir: Path,
    category_filter: str | None = None,
) -> list[dict]:
    """Load golden_dataset.json from the candidate's directory."""
    path = candidate_dir / "golden_dataset.json"
    with open(path, encoding="utf-8") as f:
        dataset = json.load(f)
    if category_filter:
        dataset = [q for q in dataset if q["category"] == category_filter]
    return dataset


def _seed_structured_data(candidate_dir: Path) -> str | None:
    """Copy candidate_seed.json → store/data/candidate.json.

    Backs up original if it exists. Returns backup path.
    """
    backup_path = None
    if os.path.exists(STRUCTURED_DATA_PATH):
        backup_path = STRUCTURED_DATA_PATH + ".eval_backup"
        shutil.copy2(STRUCTURED_DATA_PATH, backup_path)

    seed_path = candidate_dir / "candidate_seed.json"
    os.makedirs(os.path.dirname(STRUCTURED_DATA_PATH), exist_ok=True)
    shutil.copy2(str(seed_path), STRUCTURED_DATA_PATH)
    print(f"[Harness] Seeded structured data from {seed_path}")
    return backup_path


def _restore_structured_data(backup_path: str | None):
    """Restore the original candidate.json from backup."""
    if backup_path and os.path.exists(backup_path):
        shutil.move(backup_path, STRUCTURED_DATA_PATH)
        print("[Harness] Restored original structured data.")
    elif not backup_path:
        if os.path.exists(STRUCTURED_DATA_PATH):
            os.remove(STRUCTURED_DATA_PATH)


def _seed_documents(candidate_dir: Path, eval_candidate_id: str):
    """Ingest ALL document files from candidate_dir using production pipeline.

    For each file, infers doc_type from filename prefix and calls
    ingest_document() with the correct doc_type.
    """
    doc_files = _get_doc_files(candidate_dir)
    for file_path, doc_type in doc_files:
        print(f"[Harness] Ingesting {file_path.name} as '{doc_type}'...")
        ingest_document(str(file_path), eval_candidate_id, doc_type=doc_type)
    print(f"[Harness] Ingested {len(doc_files)} documents into '{eval_candidate_id}'")


def _cleanup_eval_collections(eval_candidate_id: str):
    """Delete the evaluation ChromaDB collections (chunks + summaries)."""
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    for name in [eval_candidate_id, f"{eval_candidate_id}_summaries"]:
        try:
            client.delete_collection(name=name)
            print(f"[Harness] Cleaned up collection '{name}'")
        except Exception:
            pass


def _collection_has_data(eval_candidate_id: str) -> bool:
    """True if the candidate's chunk collection already exists and is non-empty.

    Lets a resumed run skip re-ingestion (and its LLM summary calls + PNG OCR)
    when the collection from a previous run is still on disk.
    """
    try:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        return client.get_collection(name=eval_candidate_id).count() > 0
    except Exception:
        return False


# ── Pipeline runner ──────────────────────────────────────────────────────────


def _run_pipeline_on_dataset(
    dataset: list[dict],
    eval_candidate_id: str,
    candidate_name: str,
    top_k: int = 3,
) -> list[dict]:
    """Run the agent pipeline on every question and tag results with candidate info."""
    results = []
    total = len(dataset)

    for i, item in enumerate(dataset):
        question = item["question"]
        print(f"\n[Harness] ({i + 1}/{total}) [{candidate_name}] {question[:80]}...")

        start = time.time()
        try:
            pipeline_result = run_full_pipeline(
                question=question,
                candidate_id=eval_candidate_id,
                top_k=top_k,
            )
            elapsed = time.time() - start
            print(f"  → Answer: {pipeline_result['answer'][:100]}... ({elapsed:.1f}s)")
            print(f"  → Tool: {pipeline_result['final_tool']} | Route: {pipeline_result['route']}")
        except Exception as e:
            print(f"  → ERROR: {e}")
            pipeline_result = {
                "answer": f"[ERROR] {e}",
                "contexts": [],
                "tool_trajectory": [],
                "final_tool": None,
                "route": None,
            }
            elapsed = time.time() - start

        results.append(
            {
                "id": item["id"],
                "question": question,
                "answer": pipeline_result["answer"],
                "contexts": pipeline_result["contexts"],
                "fused_pool": pipeline_result.get("fused_pool"),
                "ground_truth": item["ground_truth"],
                "category": item["category"],
                "expected_source": item["expected_source"],
                "difficulty": item["difficulty"],
                "expected_route": item.get("expected_route"),
                "tool_trajectory": pipeline_result["tool_trajectory"],
                "final_tool": pipeline_result["final_tool"],
                "route": pipeline_result["route"],
                "latency_s": round(elapsed, 2),
                "candidate_id": eval_candidate_id,
                "candidate_name": candidate_name,
            }
        )

    return results


# ── Component runners ────────────────────────────────────────────────────────


def _run_tool_selection(pipeline_results: list[dict]) -> pd.DataFrame | None:
    """Evaluate whether the agent picked the expected tool."""
    from evaluation.evaluators.tool_evaluator import run_tool_evaluation

    df = run_tool_evaluation(pipeline_results)
    df.to_csv(REPORTS_DIR / "tool_selection_scores.csv", index=False)
    return df


def _run_rag_quality(pipeline_results: list[dict], judge_model: str) -> pd.DataFrame | None:
    """Evaluate RAG quality (RAGAS) on RAG-routed questions only.

    Negative questions are excluded — see ``select_rag_results``.

    NOTE: The DeepEval HallucinationMetric was removed here. It scored
    hallucination as the fraction of retrieved chunks the answer "contradicts",
    using the noisy retrieval pool as if it were authoritative ground truth and
    a weak local judge that conflated omission with contradiction — producing
    false positives (e.g. a verbatim-correct answer scored 1.0). RAGAS
    faithfulness already measures answer-grounding correctly, so this metric was
    redundant noise.
    """
    from evaluation.report import select_rag_results

    rag_data = select_rag_results(pipeline_results)
    print(f"[Harness] {len(rag_data)} questions routed through RAG (negatives excluded)")

    if not rag_data:
        print("[Harness] No RAG-routed questions — skipping RAGAS")
        return None

    from evaluation.evaluators.ragas_evaluator import run_ragas_evaluation

    ragas_df = run_ragas_evaluation(rag_data, judge_model=judge_model)
    ragas_df.to_csv(REPORTS_DIR / "ragas_scores.csv", index=False)

    return ragas_df


def _run_geval(pipeline_results: list[dict], judge_model: str) -> pd.DataFrame | None:
    """Evaluate answer correctness via GEval on all questions.

    Includes negative questions — their ground truths are expected refusal
    statements, so GEval scores whether the agent's refusal wording is correct.
    """
    print(f"[Harness] {len(pipeline_results)} questions for GEval")

    if not pipeline_results:
        return None

    from evaluation.evaluators.deepeval_evaluator import run_deepeval_geval

    df = run_deepeval_geval(pipeline_results, judge_model=judge_model)
    df.to_csv(REPORTS_DIR / "geval_scores.csv", index=False)
    return df


def _run_retrieval_gates(pipeline_results: list[dict]) -> pd.DataFrame | None:
    """Localize retrieval failures (ingestion vs recall vs rerank) per question."""
    from evaluation.evaluators.retrieval_gate_evaluator import run_retrieval_gate_evaluation

    df = run_retrieval_gate_evaluation(pipeline_results)
    if df is not None and not df.empty:
        df.to_csv(REPORTS_DIR / "retrieval_gate_scores.csv", index=False)
    return df


def _run_refusal(pipeline_results: list[dict]) -> pd.DataFrame | None:
    """Evaluate refusal behaviour on all questions.

    Checks that the agent refuses negative questions and does NOT refuse
    legitimate ones.
    """
    print(f"[Harness] {len(pipeline_results)} questions for refusal evaluation")

    if not pipeline_results:
        return None

    from evaluation.evaluators.refusal_evaluator import run_refusal_evaluation

    df = run_refusal_evaluation(pipeline_results)
    df.to_csv(REPORTS_DIR / "refusal_scores.csv", index=False)
    return df


def _run_ingestion(candidates_info: list[dict], judge_model: str) -> dict | None:
    """Run ingestion evaluation for ALL candidates.

    candidates_info: list of {"eval_id": str, "name": str, "doc_files": list}.
    Returns a dict keyed by eval_id with per-candidate reports.
    """
    from evaluation.evaluators.ingestion_evaluator import run_ingestion_evaluation

    reports = {}
    for cand in candidates_info:
        print(f"[Harness] Ingestion eval for {cand['name']} ({cand['eval_id']})")
        reports[cand["eval_id"]] = {
            "name": cand["name"],
            "report": run_ingestion_evaluation(cand["eval_id"], judge_model=judge_model),
        }

    ingestion_path = REPORTS_DIR / "ingestion_report.json"
    with open(ingestion_path, "w", encoding="utf-8") as f:
        json.dump(reports, f, indent=2, ensure_ascii=False)
    return reports


def _run_router(pipeline_results: list[dict]) -> pd.DataFrame | None:
    """Evaluate broad/specific routing accuracy."""
    router_data = [r for r in pipeline_results if r.get("expected_route") is not None]
    print(f"[Harness] {len(router_data)} questions with expected route")

    if not router_data:
        return None

    from evaluation.evaluators.router_evaluator import run_router_evaluation

    df = run_router_evaluation(router_data)
    df.to_csv(REPORTS_DIR / "router_scores.csv", index=False)
    return df


# ── Component dispatch ───────────────────────────────────────────────────────

ALL_COMPONENTS = ["tool_selection", "rag", "retrieval_gates", "geval", "refusal", "ingestion", "router"]


# ── Main entry point ────────────────────────────────────────────────────────


def run_evaluation(
    candidates: list[int] | None = None,
    components: list[str] | None = None,
    category_filter: str | None = None,
    top_k: int = 3,
    judge_model: str = "qwen3",
    dry_run: bool = False,
    report_format: str = "html",
    reuse_results: bool = False,
    resume: bool = False,
) -> dict:
    """
    Multi-candidate component-based evaluation pipeline.

    For each candidate:
      1. Seeds structured data and ingests all documents
      2. Runs the agent pipeline on their golden dataset
      3. Tags results with candidate_id/candidate_name

    Then runs component evaluations on the COMBINED result set and generates
    a report with both per-candidate and aggregate breakdowns.
    """
    if components is None:
        components = ALL_COMPONENTS

    # ── Discover candidates ─────────────────────────────────────────
    discovered = _discover_candidates(candidates)

    print("=" * 70)
    print("  MULTI-CANDIDATE EVALUATION HARNESS")
    print("=" * 70)
    print(f"  Candidates : {[c['name'] for c in discovered]}")
    print(f"  Components : {components}")
    print(f"  Judge model: {judge_model}")
    print(f"  Category   : {category_filter or 'all'}")
    print(f"  Top-K      : {top_k}")
    print(f"  Dry run    : {dry_run}")
    print(f"  Reuse      : {reuse_results}")
    print(f"  Resume     : {resume}")
    print("=" * 70)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    partial_dir = REPORTS_DIR / "partial"
    partial_dir.mkdir(parents=True, exist_ok=True)

    all_pipeline_results = []
    candidates_info = []  # for ingestion eval + reporting
    eval_candidate_ids = []  # for cleanup

    if reuse_results:
        raw_path = REPORTS_DIR / "pipeline_results.json"
        with open(raw_path, encoding="utf-8") as f:
            all_pipeline_results = json.load(f)
        if category_filter:
            all_pipeline_results = [r for r in all_pipeline_results if r["category"] == category_filter]
        # Reconstruct candidates_info from results
        seen = {}
        for r in all_pipeline_results:
            eid = r.get("candidate_id", "unknown")
            if eid not in seen:
                seen[eid] = {
                    "eval_id": eid,
                    "name": r.get("candidate_name", eid),
                    "doc_files": [],
                    "doc_count": 0,
                    "question_count": 0,
                }
            seen[eid]["question_count"] += 1
        candidates_info = list(seen.values())
        eval_candidate_ids = [c["eval_id"] for c in candidates_info]
        print(f"[Harness] Reusing {len(all_pipeline_results)} results from {raw_path}")
    else:
        # ── Run pipeline per candidate ──────────────────────────────
        backup_path = None
        start_time = time.time()

        for cand in discovered:
            print(f"\n{'=' * 70}")
            print(f"  CANDIDATE: {cand['name']} (candidate_{cand['idx']})")
            print(f"{'=' * 70}")

            eval_id = cand["eval_id"]
            eval_candidate_ids.append(eval_id)

            dataset = _load_golden_dataset(cand["dir"], category_filter)

            # Per-candidate checkpoint. Tied to the run config (top_k + category)
            # so a checkpoint from a different setting is never silently reused.
            partial_path = partial_dir / f"{eval_id}.json"
            cached = None
            if resume and partial_path.exists():
                try:
                    with open(partial_path, encoding="utf-8") as f:
                        payload = json.load(f)
                    if payload.get("top_k") == top_k and payload.get("category_filter") == category_filter:
                        cached = payload["results"]
                    else:
                        print(
                            f"[Harness] Checkpoint for {cand['name']} has different "
                            f"config (top_k/category) — re-running."
                        )
                except Exception as e:
                    print(f"[Harness] Could not read checkpoint for {cand['name']}: {e}")

            if cached is not None:
                # Skip the expensive agent QA loop; just make sure the collection
                # exists so retrieval-gate / ingestion components can read it.
                if not _collection_has_data(eval_id):
                    print(f"[Harness] Collection missing for {cand['name']} — re-ingesting.")
                    _cleanup_eval_collections(eval_id)
                    _seed_documents(cand["dir"], eval_id)
                results = cached
                print(f"[Harness] ↳ Resumed {cand['name']} from checkpoint ({len(results)} cached results)")
            else:
                # Seed structured data
                backup_path = _seed_structured_data(cand["dir"])

                # Clean + ingest documents
                _cleanup_eval_collections(eval_id)
                _seed_documents(cand["dir"], eval_id)

                # Set candidate ID for the agent
                set_candidate_id(eval_id)

                print(f"[Harness] {len(dataset)} questions for {cand['name']}")

                # Run pipeline
                results = _run_pipeline_on_dataset(dataset, eval_id, cand["name"], top_k)

                # Restore structured data, then checkpoint immediately so a later
                # crash never loses this candidate's answers.
                _restore_structured_data(backup_path)
                backup_path = None
                try:
                    with open(partial_path, "w", encoding="utf-8") as f:
                        json.dump(
                            {
                                "results": results,
                                "top_k": top_k,
                                "category_filter": category_filter,
                            },
                            f,
                            ensure_ascii=False,
                        )
                    print(f"[Harness] ✔ Checkpointed {cand['name']} → {partial_path.name}")
                except Exception as e:
                    print(f"[Harness] WARNING: failed to checkpoint {cand['name']}: {e}")

            all_pipeline_results.extend(results)

            # Track candidate info
            doc_files = _get_doc_files(cand["dir"])
            candidates_info.append(
                {
                    "idx": cand["idx"],
                    "eval_id": eval_id,
                    "name": cand["name"],
                    "doc_count": len(doc_files),
                    "question_count": len(dataset),
                    "doc_files": [(str(f), dt) for f, dt in doc_files],
                }
            )

            print(f"[Harness] ✓ {cand['name']}: {len(results)} results collected")

        pipeline_elapsed = time.time() - start_time
        print(f"\n[Harness] Pipeline completed in {pipeline_elapsed:.1f}s ({len(all_pipeline_results)} total results)")

        # Save combined results
        raw_path = REPORTS_DIR / "pipeline_results.json"
        with open(raw_path, "w", encoding="utf-8") as f:
            json.dump(all_pipeline_results, f, indent=2, ensure_ascii=False)
        print(f"[Harness] Raw results saved to {raw_path}")

    # ── Component evaluations ───────────────────────────────────────
    try:
        eval_results = {
            "pipeline_results": all_pipeline_results,
            "candidates": candidates_info,
            "tool_eval_df": None,
            "ragas_df": None,
            "retrieval_gate_df": None,
            "geval_df": None,
            "refusal_df": None,
            "ingestion_report": None,
            "router_df": None,
            "report_path": None,
        }

        if dry_run:
            print("\n[Harness] Dry run — skipping all evaluations")
        else:
            for component in components:
                print(f"\n{'─' * 50}")
                print(f"  Component: {component}")
                print("─" * 50)

                if component == "tool_selection":
                    eval_results["tool_eval_df"] = _run_tool_selection(all_pipeline_results)

                elif component == "rag":
                    eval_results["ragas_df"] = _run_rag_quality(all_pipeline_results, judge_model)

                elif component == "retrieval_gates":
                    eval_results["retrieval_gate_df"] = _run_retrieval_gates(all_pipeline_results)

                elif component == "geval":
                    eval_results["geval_df"] = _run_geval(all_pipeline_results, judge_model)

                elif component == "refusal":
                    eval_results["refusal_df"] = _run_refusal(all_pipeline_results)

                elif component == "ingestion":
                    eval_results["ingestion_report"] = _run_ingestion(candidates_info, judge_model)

                elif component == "router":
                    eval_results["router_df"] = _run_router(all_pipeline_results)

        # ── Generate report ─────────────────────────────────────────
        if not dry_run:
            from evaluation.report import generate_report

            report_path = generate_report(
                pipeline_results=all_pipeline_results,
                eval_results=eval_results,
                output_format=report_format,
            )
            eval_results["report_path"] = report_path
            print(f"\n[Harness] Report generated: {report_path}")

    finally:
        if not reuse_results:
            restore_candidate_id()
            if backup_path:
                _restore_structured_data(backup_path)
            # Cleanup all eval collections
            for eval_id in eval_candidate_ids:
                _cleanup_eval_collections(eval_id)

    print("\n" + "=" * 70)
    print("  EVALUATION COMPLETE")
    print("=" * 70)

    return eval_results
