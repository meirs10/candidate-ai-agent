"""
Unit & integration tests for the ingestion pipeline (rag/ingest.py).

Tests cover:
  - Section extraction from different file formats
  - Chunk sizing and quality
  - Metadata correctness in ChromaDB
  - Summary generation and storage
  - Doc-type breakdown across multiple documents

Run:
    pytest tests/test_ingest.py -v
    pytest tests/test_ingest.py -v -m "not integration"   # skip LLM tests
"""

import json
import pytest
import chromadb
from pathlib import Path

from rag.ingest import (
    extract_sections,
    text_splitter,
    ingest_document,
    get_collection,
    get_summary_collection,
)

# ── Test fixtures ────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).parent.parent / "evaluation" / "data"
TEST_COLLECTION = "test_ingest_unit"
CHROMA_PATH = "./chroma_db"


def _get_candidate_file(candidate_idx: int, prefix: str) -> Path:
    """Find a file in candidate_N/ dir by prefix (cv_, readme_, etc.)."""
    cand_dir = DATA_DIR / f"candidate_{candidate_idx}"
    for f in cand_dir.iterdir():
        if f.name.startswith(prefix) and f.name not in ("candidate_seed.json", "golden_dataset.json"):
            return f
    raise FileNotFoundError(f"No {prefix}* file in {cand_dir}")


@pytest.fixture(autouse=True)
def cleanup_test_collection():
    """Clean up test ChromaDB collection before and after each test."""
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    for name in [TEST_COLLECTION, f"{TEST_COLLECTION}_summaries"]:
        try:
            client.delete_collection(name=name)
        except Exception:
            pass
    yield
    for name in [TEST_COLLECTION, f"{TEST_COLLECTION}_summaries"]:
        try:
            client.delete_collection(name=name)
        except Exception:
            pass


# ── Section Extraction Tests ─────────────────────────────────────────────────


class TestExtractSections:
    """Test that extract_sections() properly parses documents into sections."""

    def test_txt_returns_sections(self):
        """TXT file with # headers should produce multiple sections."""
        cv_path = _get_candidate_file(3, "cv_")  # candidate_3 has .txt files
        sections = extract_sections(str(cv_path))

        assert len(sections) > 0, "No sections extracted from TXT file"
        assert all("text" in s and "section" in s for s in sections), \
            "Each section must have 'text' and 'section' keys"

    def test_md_returns_sections(self):
        """Markdown file with # headers should produce multiple sections."""
        cv_path = _get_candidate_file(4, "cv_")  # candidate_4 has .md files
        sections = extract_sections(str(cv_path))

        assert len(sections) > 0, "No sections extracted from MD file"
        assert all("text" in s and "section" in s for s in sections)

    def test_sections_have_meaningful_names(self):
        """Section names should come from document headers, not all be 'general'."""
        cv_path = _get_candidate_file(3, "cv_")
        sections = extract_sections(str(cv_path))

        section_names = set(s["section"] for s in sections)
        # Should have more than just "general" — headers like
        # "Work Experience", "Education", "Technical Skills" etc.
        assert len(section_names) > 1, \
            f"Expected multiple section names, got only: {section_names}"

    def test_no_empty_section_text(self):
        """No section should have empty or whitespace-only text."""
        cv_path = _get_candidate_file(3, "cv_")
        sections = extract_sections(str(cv_path))

        for s in sections:
            assert s["text"].strip(), \
                f"Section '{s['section']}' has empty text"

    def test_pdf_returns_sections(self):
        """PDF file should also produce sections."""
        cv_path = _get_candidate_file(1, "cv_")  # candidate_1 has .pdf files
        sections = extract_sections(str(cv_path))

        assert len(sections) > 0, "No sections extracted from PDF file"

    def test_docx_returns_sections(self):
        """DOCX file should also produce sections."""
        cv_path = _get_candidate_file(2, "cv_")  # candidate_2 has .docx files
        sections = extract_sections(str(cv_path))

        assert len(sections) > 0, "No sections extracted from DOCX file"

    def test_png_returns_sections(self):
        """PNG image file should produce sections via OCR."""
        cv_path = _get_candidate_file(5, "cv_")  # candidate_5 has .png files
        sections = extract_sections(str(cv_path))

        assert len(sections) > 0, "No sections extracted from PNG file"


# ── Chunk Quality Tests ──────────────────────────────────────────────────────


class TestChunkQuality:
    """Test that the text splitter produces reasonable chunks."""

    def test_chunks_within_size_limit(self):
        """No chunk should exceed chunk_size (1000 chars) by more than overlap."""
        cv_path = _get_candidate_file(3, "cv_")
        sections = extract_sections(str(cv_path))

        max_allowed = 1100  # chunk_size + overlap
        for section in sections:
            chunks = text_splitter.split_text(section["text"])
            for chunk in chunks:
                assert len(chunk) <= max_allowed, \
                    f"Chunk exceeds max size ({len(chunk)} > {max_allowed}): {chunk[:80]}..."

    def test_no_tiny_chunks(self):
        """Chunks should not be extremely small (< 10 chars) — indicates bad splitting.

        Note: unstructured may fragment some elements (e.g., phone numbers,
        dates) into tiny pieces. A few are acceptable as parser artifacts;
        many indicate a systemic splitting problem.
        """
        cv_path = _get_candidate_file(3, "cv_")
        sections = extract_sections(str(cv_path))

        tiny_chunks = []
        total_chunks = 0
        for section in sections:
            chunks = text_splitter.split_text(section["text"])
            total_chunks += len(chunks)
            for chunk in chunks:
                if len(chunk) < 10:
                    tiny_chunks.append(chunk)

        max_acceptable = max(5, int(total_chunks * 0.05))  # allow 5 or 5%
        if tiny_chunks:
            import warnings
            warnings.warn(f"Found {len(tiny_chunks)} tiny chunks (parser artifacts): {tiny_chunks}")
        assert len(tiny_chunks) <= max_acceptable, \
            f"Too many tiny chunks ({len(tiny_chunks)}/{total_chunks}): {tiny_chunks}"

    def test_no_duplicate_chunks_in_section(self):
        """Within a single section, there should be no exact duplicate chunks."""
        cv_path = _get_candidate_file(3, "cv_")
        sections = extract_sections(str(cv_path))

        for section in sections:
            chunks = text_splitter.split_text(section["text"])
            unique = set(chunks)
            assert len(chunks) == len(unique), \
                f"Section '{section['section']}' has {len(chunks) - len(unique)} duplicate chunks"


# ── Ingestion Integration Tests ──────────────────────────────────────────────


class TestIngestionIntegration:
    """Integration tests that ingest a real file and check ChromaDB state.

    These tests require Ollama running (for summary generation).
    """

    @pytest.mark.integration
    def test_ingest_creates_chunks(self):
        """Ingesting a file should create chunks in the collection."""
        cv_path = _get_candidate_file(3, "cv_")
        ingest_document(str(cv_path), TEST_COLLECTION, doc_type="cv")

        client = chromadb.PersistentClient(path=CHROMA_PATH)
        collection = client.get_or_create_collection(TEST_COLLECTION)
        data = collection.get(include=["documents", "metadatas"])

        assert len(data["documents"]) > 0, "No chunks stored after ingestion"

    @pytest.mark.integration
    def test_chunk_metadata_has_required_fields(self):
        """Every chunk should have candidate_id, doc_type, source_file, section."""
        cv_path = _get_candidate_file(3, "cv_")
        ingest_document(str(cv_path), TEST_COLLECTION, doc_type="cv")

        client = chromadb.PersistentClient(path=CHROMA_PATH)
        collection = client.get_or_create_collection(TEST_COLLECTION)
        data = collection.get(include=["metadatas"])

        required_fields = {"candidate_id", "doc_type", "source_file", "section"}
        for meta in data["metadatas"]:
            missing = required_fields - set(meta.keys())
            assert not missing, f"Chunk missing metadata fields: {missing}"

    @pytest.mark.integration
    def test_doc_type_set_correctly(self):
        """All chunks from a cv_ file should have doc_type='cv'."""
        cv_path = _get_candidate_file(3, "cv_")
        ingest_document(str(cv_path), TEST_COLLECTION, doc_type="cv")

        client = chromadb.PersistentClient(path=CHROMA_PATH)
        collection = client.get_or_create_collection(TEST_COLLECTION)
        data = collection.get(include=["metadatas"])

        for meta in data["metadatas"]:
            assert meta["doc_type"] == "cv", \
                f"Expected doc_type='cv', got '{meta['doc_type']}'"

    @pytest.mark.integration
    def test_summary_created(self):
        """Ingestion should create a summary in the _summaries collection."""
        cv_path = _get_candidate_file(3, "cv_")
        ingest_document(str(cv_path), TEST_COLLECTION, doc_type="cv")

        client = chromadb.PersistentClient(path=CHROMA_PATH)
        summary_col = client.get_or_create_collection(f"{TEST_COLLECTION}_summaries")
        data = summary_col.get(include=["documents"])

        assert len(data["documents"]) > 0, "No summary stored after ingestion"
        assert len(data["documents"][0]) > 50, \
            f"Summary too short: '{data['documents'][0][:100]}'"

    @pytest.mark.integration
    def test_multiple_docs_different_types(self):
        """Ingesting cv + readme + recommendation should store all with correct doc_types."""
        cand_dir = DATA_DIR / "candidate_3"
        cv_path = _get_candidate_file(3, "cv_")
        readme_path = _get_candidate_file(3, "readme_")
        rec_path = _get_candidate_file(3, "recommendation_")

        ingest_document(str(cv_path), TEST_COLLECTION, doc_type="cv")
        ingest_document(str(readme_path), TEST_COLLECTION, doc_type="readme")
        ingest_document(str(rec_path), TEST_COLLECTION, doc_type="recommendation")

        client = chromadb.PersistentClient(path=CHROMA_PATH)
        collection = client.get_or_create_collection(TEST_COLLECTION)
        data = collection.get(include=["metadatas"])

        doc_types = set(m["doc_type"] for m in data["metadatas"])
        assert doc_types == {"cv", "readme", "recommendation"}, \
            f"Expected all 3 doc_types, got: {doc_types}"

    @pytest.mark.integration
    def test_chunks_contain_section_prefix(self):
        """Each chunk should be contextualized with 'Section: <name>' prefix."""
        cv_path = _get_candidate_file(3, "cv_")
        ingest_document(str(cv_path), TEST_COLLECTION, doc_type="cv")

        client = chromadb.PersistentClient(path=CHROMA_PATH)
        collection = client.get_or_create_collection(TEST_COLLECTION)
        data = collection.get(include=["documents"])

        for doc in data["documents"]:
            assert doc.startswith("Section:"), \
                f"Chunk missing 'Section:' prefix: {doc[:80]}..."

    @pytest.mark.integration
    def test_no_exact_duplicate_chunks_in_collection(self):
        """No two chunks in the collection should be identical."""
        cv_path = _get_candidate_file(3, "cv_")
        ingest_document(str(cv_path), TEST_COLLECTION, doc_type="cv")

        client = chromadb.PersistentClient(path=CHROMA_PATH)
        collection = client.get_or_create_collection(TEST_COLLECTION)
        data = collection.get(include=["documents"])

        docs = data["documents"]
        unique = set(docs)
        assert len(docs) == len(unique), \
            f"Found {len(docs) - len(unique)} duplicate chunks out of {len(docs)}"
