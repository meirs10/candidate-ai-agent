"""
Document types and filename-based type inference.

Kept in its own module, separate from rag/ingest.py, because the callers that
need to *classify* a document are not the ones that need to ingest it: the setup
page renders a type dropdown per uploaded file, and scripts/reindex_profile.py
prints its plan as a dry run before deciding whether to spend anything. Neither
should pay the cost of importing `unstructured` and constructing an LLM client
just to look at a filename.

rag/ingest.py re-exports both names, so `from rag.ingest import infer_doc_type`
keeps working.
"""

from __future__ import annotations

# The candidate-facing document kinds. Each selects a summary rubric in
# rag.ingest.generate_summary.
DOC_TYPES = ("cv", "readme", "recommendation", "certificate")


def infer_doc_type(filename: str) -> str:
    """Best-effort document type from a filename, used as the default the
    candidate can correct.

    Deliberately biased away from "cv": that rubric is the one that fabricates an
    identity when applied to the wrong document, so anything unrecognised is
    treated as a project write-up instead.
    """
    low = filename.lower()
    if "recommend" in low or "reference" in low or "letter" in low:
        return "recommendation"
    if any(w in low for w in ("certificate", "transcript", "diploma", "degree",
                              "award", "grade", "תעודה", "גיליון", "אישור")):
        return "certificate"
    if "cv" in low or "resume" in low or "résumé" in low or "קורות" in low:
        return "cv"
    return "readme"
