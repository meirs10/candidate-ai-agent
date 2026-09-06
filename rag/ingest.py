import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
from unstructured.partition.auto import partition
from rag.embedder import embedder
from agent.llm import LLMClient
import os
import re

import settings as config  # module named `settings` to avoid shadowing the scorer's `config`

CHROMA_PATH = config.CHROMA_PATH  # single source of truth: settings.py

client = chromadb.PersistentClient(path=CHROMA_PATH)

# Build-time summaries use the same pluggable LLM as the rest of the app.
_llm = LLMClient()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150,
    separators=["\n\n", "\n", ". ", " ", ""],
    length_function=len,
)


def get_collection(candidate_id: str):
    return client.get_or_create_collection(
        name=candidate_id,
        metadata={"hnsw:space": "cosine"},
    )


def get_summary_collection(candidate_id: str):
    return client.get_or_create_collection(
        name=f"{candidate_id}_summaries",
        metadata={"hnsw:space": "cosine"},
    )


# -- Section extraction ------------------------------------------------------

_SPACED_HEADER_RE = re.compile(
    r"^[A-Z](\s+[A-Z]){3,}(\s+[A-Z])*\s*$"
)


def _is_spaced_header(text: str) -> bool:
    """Detect spaced-letter headers like 'T E C H N I C A L  S K I L L S'."""
    return bool(_SPACED_HEADER_RE.match(text.strip()))


# A leading section number belongs to the heading, not to the content: "6.3 The
# probabilistic router" is a section name, "GPA: 94.3" is not. Without stripping
# it first every numbered Markdown heading was read as content, and a 127 KB
# README with 99 headings collapsed into a single section.
_SECTION_NUMBER_RE = re.compile(r"^\d+(\.\d+)*[.)]?\s+")

# Longest plausible section name. Past this the partitioner has almost always
# mislabelled a narrative sentence as a Title, and adopting it as a section name
# stamps that sentence onto the front of every chunk beneath it.
_MAX_SECTION_NAME_LEN = 80


def _is_data_title(text: str) -> bool:
    """Detect Title elements that are actually content (contain numbers, colons, etc.).

    Examples that should be treated as content, not section names:
        'GPA: 94.3 🏆 Dean's Honor List (1st & 2nd Year)'
        '✉ ofir@gmail.com ☎ +972-54-2863632'
        'Three scripts delete audio permanently. Each requires an interactive yes...'
    """
    stripped = text.strip()
    if "@" in stripped or "☎" in stripped or "✉" in stripped:
        return True

    body = _SECTION_NUMBER_RE.sub("", stripped)
    if re.search(r"\d", body):
        return True
    if len(stripped) > _MAX_SECTION_NAME_LEN:
        return True
    # A complete sentence is prose the partitioner mislabelled, not a heading.
    if body.endswith(".") and len(body.split()) > 6:
        return True
    return False


def _read_utf8(file_path: str) -> str | None:
    """Return the file decoded as UTF-8, or None if it is not UTF-8 text."""
    try:
        with open(file_path, "rb") as fh:
            raw = fh.read()
        return raw.decode("utf-8-sig")
    except (UnicodeDecodeError, OSError):
        return None


def _partition_utf8_text(file_path: str, text: str):
    """Partition already-decoded text, or None if the extension isn't plain text.

    Exists because Unstructured guesses the encoding with chardet and cannot be
    told not to: partition(..., encoding="utf-8") is accepted and then silently
    dropped, since partition_md re-reads the file through its own detector. That
    detector called one perfectly valid UTF-8 README windows-1251 and mangled
    every non-ASCII character in it. Handing the partitioner a decoded string
    removes the guess entirely.
    """
    name = os.path.basename(file_path)
    ext = os.path.splitext(file_path)[1].lower()

    if ext in (".md", ".markdown"):
        from unstructured.partition.md import partition_md
        return partition_md(text=text, metadata_filename=name)
    if ext in (".txt", ".text"):
        from unstructured.partition.text import partition_text
        return partition_text(text=text, metadata_filename=name)
    return None


def extract_sections(file_path: str) -> list[dict]:
    """Partition the document into sections using Unstructured.

    Returns a list of {text, section} dicts where consecutive elements
    under the same section are merged into a single text block.
    """
    elements = None
    text = _read_utf8(file_path)
    if text is not None:
        elements = _partition_utf8_text(file_path, text)
    # Everything else — PDF, DOCX, and any genuinely non-UTF-8 file — goes
    # through the normal detection path.
    if elements is None:
        elements = partition(file_path)

    sections = []
    current_section = "general"
    current_texts = []

    def _flush():
        if current_texts:
            sections.append({
                "text": "\n\n".join(current_texts),
                "section": current_section,
            })
            current_texts.clear()

    for element in elements:
        text = element.text.strip() if element.text else ""
        if not text:
            continue

        if _is_spaced_header(text):
            _flush()
            current_section = text
            continue

        if element.category == "Title":
            if _is_data_title(text):
                current_texts.append(text)
            else:
                _flush()
                current_section = text
        else:
            current_texts.append(text)

    _flush()

    return sections


# -- Document type -----------------------------------------------------------

# Re-exported: these live in a dependency-free module so callers that only need
# to classify a filename (the setup page, reindex_profile's dry run) don't have
# to import `unstructured` and build an LLM client to do it.
from rag.ingest_types import DOC_TYPES, infer_doc_type  # noqa: E402,F401


# -- Summary generation ------------------------------------------------------

# Never let a refusal reach the summary index. Every rubric below ends with this
# because the summaries ARE the broad-query answer path: a stored "I cannot
# summarize this" is retrieved and read out when a recruiter asks the single most
# likely opening question, "tell me about the candidate".
_SUMMARY_CONTRACT = (
    "Summarize only what the document actually contains. Never refuse, never ask "
    "for a different document, and never say the document is the wrong kind — if "
    "a point below is absent, simply leave it out and summarize the rest.\n"
    "Be factual, no opinions. Output the summary text only.\n\n"
)


def generate_summary(full_text: str, doc_type: str) -> str:
    """Ask the LLM to summarize the document in 5-6 sentences.

    The rubric follows doc_type, because a rubric demanding a name, a degree and
    years of experience is unanswerable for anything that is not a CV. Applying
    it to a project write-up produced summaries like "Unable to provide requested
    summary" and, worse, ones that invented a candidate identity from whatever
    name appeared in the text.
    """
    if doc_type == "project":
        rubric = (
            "You are summarizing the documentation of a software project for a "
            "recruiter who wants a quick overview of the system.\n"
            "Write a concise 5-6 sentence summary covering:\n"
            "1. What the project is and what problem it solves\n"
            "2. Its overall architecture\n"
            "3. Its standout capability\n"
            "4. The main technology stack\n"
            "5. How it is evaluated and deployed\n"
        )
    elif doc_type == "cv":
        rubric = (
            "You are summarizing a candidate's CV for a recruiter.\n"
            "Write a concise 5-6 sentence summary covering:\n"
            "1. Candidate's full name and current/most recent role\n"
            "2. Education: degree(s), institution(s), and graduation year(s)\n"
            "3. Total years of professional experience\n"
            "4. Key technical skills and domain expertise\n"
            "5. Most notable achievement or project\n"
        )
    elif doc_type == "recommendation":
        rubric = (
            "You are summarizing a recommendation letter about a job candidate "
            "for a recruiter.\n"
            "Write a concise 4-5 sentence summary covering:\n"
            "1. Who wrote it and in what capacity they worked with the candidate\n"
            "2. The specific work or project they describe\n"
            "3. The strengths they attest to, with any concrete detail given\n"
        )
    elif doc_type == "certificate":
        rubric = (
            "You are summarizing a certificate, transcript or award belonging to "
            "a job candidate, for a recruiter.\n"
            "Write a concise 3-4 sentence summary covering:\n"
            "1. What the document certifies, and the issuing body\n"
            "2. Any grades, scores, honours or dates it records\n"
            "3. The subject area it evidences\n"
        )
    else:
        # readme / project write-ups authored BY the candidate about their own
        # work, and any unclassified document. The subject is the work, not the
        # person — asking for a CV summary here is what produced the refusals.
        rubric = (
            "You are summarizing one of a job candidate's own project write-ups "
            "for a recruiter assessing their engineering work.\n"
            "Write a concise 4-6 sentence summary covering:\n"
            "1. What the project does and the problem it solves\n"
            "2. The technical approach and the notable engineering decisions\n"
            "3. The technologies used\n"
            "4. Any measured results the document reports\n"
            "Describe the WORK. Do not try to infer the candidate's identity, "
            "employment history or education from it, and do not attribute the "
            "project to any name mentioned in the text.\n"
        )

    return _llm.complete(rubric + _SUMMARY_CONTRACT
                         + f"Document:\n{full_text[:3000]}").strip()


# -- In-memory ingestion (raw text, no file, no summary) ---------------------

def ingest_text(text: str, candidate_id: str, doc_id: str, doc_type: str = "cv") -> int:
    """Ingest a raw in-memory text document (no file partitioning, no summary).

    Used when the source is already plain text (e.g. the skill estimator ingests
    the synthetic corpus straight from documents_db.json). Every chunk stores its
    `doc_id` in the metadata so retrieval results can be traced back to their
    source document — this provenance is what makes retrieval evaluation against
    the evidence ground truth possible. Chunks are stored verbatim so the scorer
    sees the exact text. Returns the number of chunks added.
    """
    if not text or not text.strip():
        return 0

    collection = get_collection(candidate_id)
    chunks = text_splitter.split_text(text)
    if not chunks:
        return 0

    ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
    metas = [
        {"candidate_id": candidate_id, "doc_id": doc_id, "doc_type": doc_type}
        for _ in chunks
    ]
    embeddings = embedder.encode_documents(chunks)
    collection.add(documents=chunks, embeddings=embeddings, ids=ids, metadatas=metas)
    return len(chunks)


# -- Ingestion pipeline -------------------------------------------------------

def ingest_document(file_path: str, candidate_id: str, doc_type: str = "cv",
                    build_summary: bool = True):
    """Full pipeline: file -> sections -> chunks -> embeddings -> ChromaDB.

    Uses encode_documents() so all stored vectors have the 'search_document:'
    prefix baked in — aligned with encode_query() used at retrieval time.

    build_summary controls the secondary summary index (consumed by the recruiter
    agent's broad/summary retrieval path). Turn it off when the summary index
    isn't needed (e.g. ingesting purely to feed the skill scorer).
    """
    sections = extract_sections(file_path)
    if not sections:
        print(f"Warning: No content extracted from {file_path}")
        return

    collection = get_collection(candidate_id)
    base = os.path.basename(file_path)

    # --- Chunk index ---
    all_chunks, all_ids, all_metas = [], [], []

    for s_idx, section in enumerate(sections):
        chunks = text_splitter.split_text(section["text"])

        for c_idx, chunk in enumerate(chunks):
            contextualized_chunk = f"Section: {section['section']}\n{chunk}"
            all_chunks.append(contextualized_chunk)
            all_ids.append(f"{base}_s{s_idx}_chunk_{c_idx}")
            all_metas.append({
                "candidate_id": candidate_id,
                "doc_type": doc_type,
                "source_file": base,
                "section": section["section"],
                # doc_id provenance (mirrors ingest_text) so retrieved chunks can
                # always be traced back to a source document, regardless of path.
                "doc_id": base,
            })

    # encode_documents applies 'search_document:' prefix to every chunk
    all_embeddings = embedder.encode_documents(all_chunks)

    collection.add(
        documents=all_chunks,
        embeddings=all_embeddings,
        ids=all_ids,
        metadatas=all_metas,
    )
    print(f"Ingested {len(all_chunks)} chunks from {base} ({len(sections)} sections)")

    if not build_summary:
        return

    # --- Summary index ---
    full_text = " ".join(s["text"] for s in sections)
    summary = generate_summary(full_text, doc_type)

    summary_collection = get_summary_collection(candidate_id)

    # Summary is also a document being stored — use encode_documents
    summary_embedding = embedder.encode_documents([summary])

    summary_collection.add(
        documents=[summary],
        embeddings=summary_embedding,
        ids=[base],
        metadatas=[{
            "candidate_id": candidate_id,
            "doc_type": doc_type,
            "source_file": base,
        }],
    )
    print(f"Summary stored for {base}: '{summary[:80]}...'")