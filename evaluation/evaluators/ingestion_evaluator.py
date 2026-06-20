"""
Ingestion Quality Evaluator — inspects the ChromaDB state after ingestion
to assess chunk quality, section coverage, summary quality, and embedding coverage.
"""

import re

import chromadb
import numpy as np
import ollama

from rag.embedder import embedder

CHROMA_PATH = "./chroma_db"


def run_ingestion_evaluation(
    candidate_id: str,
    judge_model: str = "qwen3",
) -> dict:
    """
    Evaluate the quality of ingested data in ChromaDB.

    Args:
        candidate_id: The collection name to inspect.
        judge_model: Ollama model for LLM-judged summary quality.

    Returns:
        Dict with keys:
            chunk_stats, section_coverage, duplicate_check,
            summary_quality, embedding_probes
    """
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    report = {}

    # ── 1. Chunk Statistics ──────────────────────────────────────────
    try:
        collection = client.get_or_create_collection(
            name=candidate_id,
            metadata={"hnsw:space": "cosine"},
        )
        all_data = collection.get(include=["documents", "metadatas"])
        documents = all_data["documents"] or []
        metadatas = all_data["metadatas"] or []
    except Exception as e:
        print(f"[Ingestion Eval] Error loading collection: {e}")
        return {"error": str(e)}

    if not documents:
        print("[Ingestion Eval] No chunks found in collection!")
        return {"error": "Empty collection", "chunk_stats": {"total_chunks": 0}}

    chunk_sizes = [len(doc) for doc in documents]
    empty_chunks = sum(1 for s in chunk_sizes if s < 10)

    report["chunk_stats"] = {
        "total_chunks": len(documents),
        "avg_chunk_size": round(np.mean(chunk_sizes), 1),
        "min_chunk_size": min(chunk_sizes),
        "max_chunk_size": max(chunk_sizes),
        "std_chunk_size": round(float(np.std(chunk_sizes)), 1),
        "empty_or_tiny_chunks": empty_chunks,
    }
    print(f"[Ingestion Eval] Chunk stats: {report['chunk_stats']}")

    # ── 1b. Per-doc-type breakdown ───────────────────────────────────
    doc_type_groups = {}
    for doc, meta in zip(documents, metadatas, strict=False):
        dt = meta.get("doc_type", "unknown") if meta else "unknown"
        doc_type_groups.setdefault(dt, []).append(len(doc))

    doc_type_breakdown = {}
    for dt, sizes in sorted(doc_type_groups.items()):
        doc_type_breakdown[dt] = {
            "chunk_count": len(sizes),
            "avg_size": round(np.mean(sizes), 1),
            "min_size": min(sizes),
            "max_size": max(sizes),
        }
    report["doc_type_breakdown"] = doc_type_breakdown
    print(f"[Ingestion Eval] Doc type breakdown: { {k: v['chunk_count'] for k, v in doc_type_breakdown.items()} }")

    # ── 2. Section Coverage ──────────────────────────────────────────
    expected_sections = {
        "Personal Information",
        "Summary",
        "Work Experience",
        "Education",
        "Technical Skills",
        "Projects",
        "Certifications",
        "Languages",
        "Interests",
    }

    found_sections = set()
    for meta in metadatas:
        if meta and "section" in meta:
            # Strip markdown heading prefixes for comparison
            section = meta["section"].lstrip("#").strip()
            found_sections.add(section)

    # Case-insensitive matching
    normalized_expected = {s.lower(): s for s in expected_sections}
    normalized_found = {s.lower(): s for s in found_sections}

    matched = set(normalized_expected.keys()) & set(normalized_found.keys())
    missing_sections = {normalized_expected[k] for k in set(normalized_expected.keys()) - matched}
    extra_sections = {normalized_found[k] for k in set(normalized_found.keys()) - set(normalized_expected.keys())}

    report["section_coverage"] = {
        "expected": sorted(expected_sections),
        "found": sorted(found_sections),
        "missing": sorted(missing_sections),
        "extra": sorted(extra_sections),
        "coverage_pct": round(len(matched) / len(expected_sections) * 100, 1) if expected_sections else 0,
        "has_section_metadata": len(found_sections) > 0,
    }
    print(f"[Ingestion Eval] Section coverage: {report['section_coverage']['coverage_pct']}%")

    # ── 3. Duplicate Check ───────────────────────────────────────────
    unique_docs = set(documents)
    duplicate_count = len(documents) - len(unique_docs)

    # Near-duplicate check: chunks with >90% character overlap
    near_duplicates = 0
    doc_list = list(documents)
    for i in range(min(len(doc_list), 50)):  # cap at 50 to avoid O(n²) on large sets
        for j in range(i + 1, min(len(doc_list), 50)):
            shorter = min(len(doc_list[i]), len(doc_list[j]))
            if shorter == 0:
                continue
            # Simple character overlap ratio
            common = sum(1 for a, b in zip(doc_list[i], doc_list[j], strict=False) if a == b)
            overlap = common / shorter
            if overlap > 0.9:
                near_duplicates += 1

    report["duplicate_check"] = {
        "exact_duplicates": duplicate_count,
        "near_duplicates_sampled": near_duplicates,
        "total_unique": len(unique_docs),
    }
    print(f"[Ingestion Eval] Duplicates: {duplicate_count} exact, {near_duplicates} near")

    # ── 4. Summary Quality (LLM-judged) ──────────────────────────────
    try:
        summary_collection = client.get_or_create_collection(
            f"{candidate_id}_summaries",
            metadata={"hnsw:space": "cosine"},
        )
        summary_data = summary_collection.get(include=["documents"])
        summaries = summary_data["documents"] or []
    except Exception:
        summaries = []

    if summaries:
        summary_text = summaries[0]
        checklist = [
            "candidate name",
            "current role/job title",
            "key technical skills",
            "education/degree",
            "years of experience",
        ]
        prompt = (
            f"You are evaluating the quality of a candidate profile summary.\n\n"
            f"Summary:\n{summary_text}\n\n"
            f"Check if the summary mentions each of these key facts:\n"
            + "\n".join(f"  - {item}" for item in checklist)
            + "\n\nFor each item, respond with YES or NO. "
            "Then give an overall quality score from 0.0 to 1.0.\n\n"
            "Format your response EXACTLY as:\n"
            "candidate name: YES/NO\n"
            "current role/job title: YES/NO\n"
            "key technical skills: YES/NO\n"
            "education/degree: YES/NO\n"
            "years of experience: YES/NO\n"
            "SCORE: 0.X"
        )
        response = ollama.chat(
            model=judge_model,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response["message"]["content"].strip()

        # Parse the score
        score = None
        items_found = 0
        for line in raw.splitlines():
            line = line.strip().upper()
            if "SCORE:" in line:
                try:
                    raw_score = line.split("SCORE:")[-1].strip()
                    # Handle "0.9 / 1.0" format from Qwen3
                    raw_score = raw_score.split("/")[0].strip()
                    score = float(raw_score)
                except ValueError:
                    pass
            elif ": YES" in line:
                items_found += 1

        report["summary_quality"] = {
            "summary_exists": True,
            "summary_length": len(summary_text),
            "checklist_items_found": items_found,
            "checklist_total": len(checklist),
            "llm_score": score,
            "raw_evaluation": raw[:500],
        }
        print(f"[Ingestion Eval] Summary quality: {items_found}/{len(checklist)} items, score={score}")
    else:
        report["summary_quality"] = {
            "summary_exists": False,
            "summary_length": 0,
            "checklist_items_found": 0,
            "checklist_total": 5,
            "llm_score": 0.0,
            "raw_evaluation": "No summary found in _summaries collection",
        }
        print("[Ingestion Eval] No summary found!")

    # ── 5. Embedding Coverage Probes ─────────────────────────────────
    # Extract candidate-specific probe terms from actual documents
    def _extract_probe_terms(docs: list[str], n_terms: int = 10) -> list[str]:
        """Extract real terms from ingested docs for probing."""
        term_counts = {}
        skip = {
            "Section",
            "The",
            "This",
            "And",
            "For",
            "With",
            "From",
            "That",
            "Not",
            "Has",
            "Was",
            "Are",
            "His",
            "Her",
            "Its",
            "Our",
        }
        for doc in docs:
            for match in re.finditer(r"\b[A-Z][a-zA-Z+#.]{2,}(?:\s+[A-Z][a-zA-Z+#.]+)*\b", doc):
                term = match.group()
                if term not in skip:
                    term_counts[term] = term_counts.get(term, 0) + 1
        sorted_terms = sorted(term_counts, key=term_counts.get, reverse=True)
        return sorted_terms[:n_terms]

    probe_terms = _extract_probe_terms(documents)
    probe_results = []

    for term in probe_terms:
        q_embedding = [embedder.encode_query(term)]
        results = collection.query(query_embeddings=q_embedding, n_results=1)
        top_doc = results["documents"][0][0] if results["documents"] and results["documents"][0] else ""
        found = term.lower() in top_doc.lower()
        probe_results.append(
            {
                "term": term,
                "found_in_top1": found,
                "top1_preview": top_doc[:100],
            }
        )

    hit_rate = sum(1 for p in probe_results if p["found_in_top1"]) / len(probe_results)
    report["embedding_probes"] = {
        "probes": probe_results,
        "hit_rate": round(hit_rate, 3),
    }
    print(f"[Ingestion Eval] Embedding probe hit rate: {hit_rate * 100:.1f}%")

    return report
