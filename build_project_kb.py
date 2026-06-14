"""
build_project_kb.py — Ingest the project overview into its own ChromaDB
collection so the recruiter agent's `search_project` tool can answer questions
about the system itself.

Run once locally (and whenever you edit store/data/project/project_overview.txt),
with the SAME embedding provider you serve with, so the project index matches the
query embeddings:

    EMBED_PROVIDER=voyage RERANK_PROVIDER=voyage \
    ANTHROPIC_API_KEY=... VOYAGE_API_KEY=... \
    python build_project_kb.py

This populates the `project_kb` (and `project_kb_summaries`) collections inside
./chroma_db, which then ships with the deployment alongside the candidate index.
"""

import chromadb

from agent.tools import PROJECT_ID
from rag.ingest import CHROMA_PATH, ingest_document

PROJECT_DOC = "store/data/project/project_overview.txt"


def main():
    # Rebuild from scratch so re-runs don't duplicate chunks.
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    for name in (PROJECT_ID, f"{PROJECT_ID}_summaries"):
        try:
            client.delete_collection(name=name)
            print(f"[ProjectKB] Cleared existing collection '{name}'")
        except Exception:
            pass

    print(f"[ProjectKB] Ingesting {PROJECT_DOC} into '{PROJECT_ID}'...")
    ingest_document(PROJECT_DOC, PROJECT_ID, doc_type="project", build_summary=True)
    print("[ProjectKB] Done. The search_project tool can now answer project questions.")


if __name__ == "__main__":
    main()
