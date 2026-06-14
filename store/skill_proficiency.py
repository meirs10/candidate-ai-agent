"""
skill_proficiency.py – Bridge: candidate documents → estimated skill levels.

For each skill the candidate listed, this retrieves the skill's evidence chunks
from the candidate's ingested documents (routing/summary OFF — a skill name is
always a *specific* query, so it goes straight through the fusion path) and runs
the trained scoring model to estimate a 1-5 proficiency level.

The result (level + the evidence chunks it was based on) is what gets persisted
into the structured store, so the recruiter agent can later surface a verified,
model-grounded proficiency instead of guessing from free-text retrieval.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from rag.retriever import retrieve_batch_for_training

# Make the nested estimator's scoring_model package importable (it uses flat
# imports internally: `import config`, `import heads`, `import model`).
_REPRESENTOR_ROOT = Path(__file__).resolve().parent.parent
_SCORING_DIR = _REPRESENTOR_ROOT / "skill_proficiency_estimator" / "scoring_model"
if str(_SCORING_DIR) not in sys.path:
    sys.path.insert(0, str(_SCORING_DIR))

import predict  # noqa: E402  (import after sys.path setup, by design)


def _free_ollama_vram() -> None:
    """Ask the Ollama server to evict its model from VRAM so the memory-heavy
    DeBERTa scorer gets the GPU to itself for the brief scoring window.

    Only relevant for the local Ollama LLM stack — with OLLAMA_NUM_PARALLEL the
    resident model can occupy most of the card. The model reloads automatically
    (honoring NUM_PARALLEL) on the next agent/judge call, so the QA loop is
    unaffected. No-op for the API stack (no Ollama in play).
    """
    import settings
    if settings.LLM_PROVIDER != "ollama":
        return
    model = settings.OLLAMA_MODEL
    # Ollama unloads a model immediately when sent a request with keep_alive=0
    # and no prompt (documented behavior). Try the client, fall back to raw HTTP.
    try:
        import ollama
        ollama.generate(model=model, prompt="", keep_alive=0)
        return
    except Exception:
        pass
    try:
        import json
        import urllib.request
        req = urllib.request.Request(
            "http://localhost:11434/api/generate",
            data=json.dumps({"model": model, "keep_alive": 0}).encode(),
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=30).read()
    except Exception as e:
        print(f"[skill] could not unload Ollama model: {e}")

# Chunks ingested via ingest_document() carry a "Section: <name>\n" prefix for
# retrieval context. The scorer was trained on raw chunk text (no such prefix),
# so we strip it before scoring to keep inputs in the training distribution.
_SECTION_PREFIX = re.compile(r"^Section: .*?\n")


def _for_scoring(chunk: str) -> str:
    return _SECTION_PREFIX.sub("", chunk, count=1)


def estimate_skills(
    candidate_id: str,
    skills: list[str],
    top_k: int | None = None,
) -> list[dict]:
    """Estimate proficiency for each candidate-listed skill from their documents.

    Parameters
    ----------
    candidate_id : the per-candidate ChromaDB collection to retrieve from.
    skills       : the skills the candidate listed (free text).
    top_k        : evidence chunks per skill (defaults to the model's
                   training-time RETRIEVE_TOP_K so the scorer sees the same shape).

    Returns
    -------
    list[dict], one per skill in input order:
        {"skill": str, "level": int (1-5), "chunks": list[str], "doc_ids": list}
    """
    skills = [s.strip() for s in skills if s and s.strip()]
    if not skills:
        return []

    k = top_k or predict.RETRIEVE_TOP_K

    # One batched retrieval pass over all skills (fusion + doc_id provenance).
    retrievals = retrieve_batch_for_training(skills, candidate_id, top_k=k)

    # Score on section-stripped chunks; store the original chunks as evidence.
    items = [
        (skill, [_for_scoring(c) for c in r["chunks"]])
        for skill, r in zip(skills, retrievals)
    ]
    # Hand the GPU to DeBERTa for the scoring burst (evict Ollama), then give it
    # back so the QA loop's Ollama can reload with full OLLAMA_NUM_PARALLEL.
    _free_ollama_vram()
    try:
        levels = predict.predict_levels(items)
    finally:
        predict.unload()

    results: list[dict] = []
    for skill, r, level in zip(skills, retrievals, levels):
        results.append({
            "skill": skill,
            "level": level,
            "chunks": r["chunks"],
            "doc_ids": r.get("doc_ids", []),
        })
    return results
