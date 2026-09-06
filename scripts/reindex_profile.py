"""
Rebuild the document index from a folder, with an explicit document type per file.

Why this exists: ingestion writes deterministic ids (`<file>_s<n>_chunk_<n>`, and
the filename itself for the summary), and ChromaDB silently ignores a write to an
id that already exists. So simply re-uploading a document does NOT replace a bad
summary or re-file a document that went into the wrong collection — the original
entry wins. Fixing either requires deleting first, which is what this does.

Document type selects the summary rubric (rag/ingest.generate_summary): a CV is
summarised by who the candidate is, a project write-up by what the work does.

Everything here goes into the CANDIDATE's collection. The project knowledge base
is a separate, build-time concern — it describes the system rather than any
candidate, and is built from store/data/project/project_overview.txt by
build_project_kb.py.

Usage:
    python -m scripts.reindex_profile <folder> [--apply]

Without --apply it is a dry run: it prints the plan and makes no API calls and no
writes. Types are inferred from the filename and can be corrected with --type:

    python -m scripts.reindex_profile "docs" --apply \
        --type "Letter from Dr Cohen.pdf=recommendation"
"""

from __future__ import annotations

import argparse
import os
import sys

import chromadb

import settings as config

# Types and inference come from rag.ingest so this script and the setup page
# cannot disagree about what a given filename is. They had already drifted: the
# copy that used to live here missed "letter", "diploma" and "degree", and
# checked "cv" before "recommendation", so "CV recommendation letter.pdf" was
# typed differently depending on which entry point you used.
from rag.ingest_types import DOC_TYPES as VALID_TYPES, infer_doc_type as infer_type


def purge(client, collection_name: str, source_files: list[str]) -> int:
    """Delete every chunk and summary belonging to these source files."""
    removed = 0
    for name in (collection_name, f"{collection_name}_summaries"):
        try:
            col = client.get_collection(name)
        except Exception:
            continue
        got = col.get(include=["metadatas"])
        ids = [i for i, m in zip(got["ids"], got["metadatas"] or [])
               if (m or {}).get("source_file") in source_files
               or i in source_files]           # summaries are keyed by filename
        if ids:
            col.delete(ids=ids)
            removed += len(ids)
    return removed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--apply", action="store_true",
                    help="actually delete + re-ingest (costs embedding and LLM calls)")
    ap.add_argument("--type", action="append", default=[], metavar="FILE=TYPE",
                    help=f"override inferred type; one of {', '.join(VALID_TYPES)}")
    args = ap.parse_args()

    overrides = {}
    for spec in args.type:
        if "=" not in spec:
            print(f"[FAIL] bad --type {spec!r}, expected FILE=TYPE"); return 1
        f, t = spec.rsplit("=", 1)
        if t not in VALID_TYPES:
            print(f"[FAIL] unknown type {t!r}; valid: {', '.join(VALID_TYPES)}"); return 1
        overrides[f] = t

    if not os.path.isdir(args.folder):
        print(f"[FAIL] not a folder: {args.folder}"); return 1

    files = sorted(f for f in os.listdir(args.folder)
                   if os.path.isfile(os.path.join(args.folder, f))
                   and not f.endswith(".bak"))
    if not files:
        print(f"[FAIL] no files in {args.folder}"); return 1

    plan = [(f, overrides.get(f, infer_type(f))) for f in files]

    print("=" * 72)
    print("PLAN" + ("" if args.apply else "   (dry run — nothing will be changed)"))
    print("=" * 72)
    for f, t in plan:
        print(f"  {t:<14} -> {f}")
    unknown = [f for f, t in plan if f not in overrides and t == "readme"]
    if unknown:
        print("\n  note: these were inferred as project write-ups; override with "
              "--type if wrong:")
        for f in unknown:
            print(f"    {f}")

    if not args.apply:
        print("\nRe-run with --apply to delete the existing entries and re-ingest.")
        return 0

    client = chromadb.PersistentClient(path=config.CHROMA_PATH)

    # Delete first. Without this the re-ingest is a no-op for anything already
    # present: ChromaDB keeps the original row for an id that already exists, so
    # a stale summary would survive its own replacement.
    print("\n-- purging existing entries --")
    n = purge(client, config.CANDIDATE_ID, [f for f, _ in plan])
    print(f"  removed {n} entr(ies) from {config.CANDIDATE_ID} "
          f"/ {config.CANDIDATE_ID}_summaries")

    print("\n-- re-ingesting --")
    from rag.ingest import ingest_document          # imported late: pulls unstructured

    ok = 0
    for f, t in plan:
        path = os.path.join(args.folder, f)
        try:
            ingest_document(path, config.CANDIDATE_ID, doc_type=t)
            print(f"  [OK]   {f}  ({t} -> {config.CANDIDATE_ID})")
            ok += 1
        except Exception as e:
            print(f"  [FAIL] {f}: {type(e).__name__}: {e}")

    print(f"\n{ok}/{len(plan)} documents indexed.")
    for name in (config.CANDIDATE_ID, f"{config.CANDIDATE_ID}_summaries"):
        try:
            print(f"  {name}: {client.get_collection(name).count()}")
        except Exception:
            print(f"  {name}: missing")
    return 0


if __name__ == "__main__":
    sys.exit(main())
