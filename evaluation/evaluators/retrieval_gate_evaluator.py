"""
Per-gate retrieval evaluator — localizes *where* a relevant chunk is lost in the
retrieval pipeline, instead of only reporting an aggregate context-recall number.

The specific-route retriever has three sequential gates a relevant chunk must pass:

    Gate 1  INGESTION : a chunk that covers the answer exists in the index at all
    Gate 2  RECALL    : that chunk enters the fused candidate pool (vector + BM25 + RRF)
    Gate 3  RERANK    : that chunk survives the cross-encoder cut into the final top-k

For each specific, docs-routed question we identify the index chunk that best covers
the ground-truth answer (max cosine similarity, using the same nomic embeddings the
retriever stores), then follow that exact chunk through the captured stages:

    loss_stage = "ingestion"  if even the best index chunk is a weak match (< threshold)
               = "recall"     if it exists in the index but never entered the fused pool
               = "rerank"     if it entered the fused pool but was cut by the reranker
               = "ok"         if it reached the final retrieved context

This turns "context_recall is 0.55, why?" into a count of how many failures are an
ingestion problem vs. a recall problem vs. a reranking problem — each of which has a
different fix.

Requires ``fused_pool`` to be present on the pipeline results (captured during the
agent run). Re-run the pipeline if you are reusing older results without it.
"""

import numpy as np
import pandas as pd

from rag.embedder import embedder
# Reuse the retriever's existing Chroma client — opening a second PersistentClient
# on the same path in the same process can conflict.
from rag.retriever import client as chroma_client


def _classify(in_index: bool, in_fused: bool, in_final: bool) -> str:
    if not in_index:
        return "ingestion"
    if not in_fused:
        return "recall"
    if not in_final:
        return "rerank"
    return "ok"


def _load_index(client, candidate_id: str):
    """Return (documents, normalized-embedding matrix) for a candidate collection.

    Reads the embeddings Chroma already stored at ingestion time, so we compare
    against the exact vectors the retriever ranks on (no re-embedding of chunks).
    """
    try:
        collection = client.get_collection(name=candidate_id)
        got = collection.get(include=["documents", "embeddings"])
    except Exception as e:
        print(f"  [RetrievalGate] could not load collection '{candidate_id}': {e}")
        return None, None

    docs = got.get("documents") or []
    embs = got.get("embeddings")
    if docs is None or embs is None or len(docs) == 0 or len(embs) == 0:
        return None, None

    mat = np.asarray(embs, dtype=np.float32)
    return docs, mat


def run_retrieval_gate_evaluation(
    data: list[dict],
    sim_threshold: float = 0.5,
) -> pd.DataFrame:
    """
    Localize retrieval failures per question.

    Args:
        data: pipeline result dicts. Only specific-route, docs-routed, non-negative
              questions that carry a ``fused_pool`` are analyzed.
        sim_threshold: minimum cosine similarity between the ground truth and the
              best index chunk for Gate 1 (ingestion) to count as passed. Below this,
              the answer is judged not to be well represented by any single chunk.

    Returns:
        DataFrame with one row per analyzed question.
    """
    _RAG_TOOLS = ("search_documents", "search_project")
    eligible = [
        r for r in data
        if r.get("final_tool") in _RAG_TOOLS
        and r.get("route") == "specific"
        and r.get("category") != "negative"
        and r.get("fused_pool") is not None
        and r.get("contexts")
    ]

    skipped_no_trace = sum(
        1 for r in data
        if r.get("final_tool") in _RAG_TOOLS
        and r.get("route") == "specific"
        and r.get("category") != "negative"
        and r.get("fused_pool") is None
    )
    if skipped_no_trace:
        print(
            f"  [RetrievalGate] {skipped_no_trace} specific questions had no fused_pool "
            f"trace — re-run the pipeline (not REUSE) to capture it."
        )

    if not eligible:
        print("[RetrievalGate] No eligible questions with retrieval trace — skipping.")
        return pd.DataFrame()

    index_cache: dict[str, tuple] = {}

    rows = []
    for r in eligible:
        cand = r.get("candidate_id", "")
        if cand not in index_cache:
            index_cache[cand] = _load_index(chroma_client, cand)
        docs, mat = index_cache[cand]
        if docs is None:
            continue

        gt = str(r["ground_truth"])
        gt_vec = np.asarray(embedder.encode_query(gt), dtype=np.float32)
        sims = mat @ gt_vec  # both L2-normalized → cosine similarity
        best = int(np.argmax(sims))
        target_chunk = docs[best]
        target_sim = float(sims[best])

        fused = set(r.get("fused_pool") or [])
        final = set(r.get("contexts") or [])

        in_index = target_sim >= sim_threshold
        in_fused = target_chunk in fused
        in_final = target_chunk in final
        loss_stage = _classify(in_index, in_fused, in_final)

        rows.append({
            "question_id": r.get("id", ""),
            "candidate_name": r.get("candidate_name", ""),
            "category": r.get("category", ""),
            "difficulty": r.get("difficulty", ""),
            "question": r.get("question", ""),
            "target_sim": round(target_sim, 3),
            "in_index": in_index,
            "in_fused_pool": in_fused,
            "in_final": in_final,
            "loss_stage": loss_stage,
            "fused_pool_size": len(fused),
            "target_chunk": target_chunk[:160],
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    counts = df["loss_stage"].value_counts().to_dict()
    total = len(df)
    ok = counts.get("ok", 0)
    print(f"[RetrievalGate] Analyzed {total} specific docs questions.")
    print(f"  reached final context (ok): {ok}/{total} ({ok/total*100:.1f}%)")
    for stage in ("ingestion", "recall", "rerank"):
        n = counts.get(stage, 0)
        if n:
            print(f"  lost at {stage:9s}: {n} ({n/total*100:.1f}%)")
    return df
