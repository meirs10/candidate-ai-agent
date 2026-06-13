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
    levels = predict.predict_levels(items)

    results: list[dict] = []
    for skill, r, level in zip(skills, retrievals, levels):
        results.append({
            "skill": skill,
            "level": level,
            "chunks": r["chunks"],
            "doc_ids": r.get("doc_ids", []),
        })
    return results
