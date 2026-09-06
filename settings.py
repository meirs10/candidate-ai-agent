"""
config.py — Single source of truth for runtime configuration.

Everything (LLM provider, embeddings provider, reranker provider, API keys, the
deployment mode, and the recruiter access code) is resolved here, in this order:

    1. Environment variable        (loaded from the single local secrets file,
                                     .env at the repo root — see .env.example;
                                     also how CI / the eval harness / RunPod set them)
    2. Streamlit secrets           (only path for Streamlit Community Cloud / HF
                                     Spaces — those platforms have no local .env;
                                     paste the same keys into their Secrets UI)
    3. Hard-coded default          (Option A: all-API, production-safe)

This is what makes the project *pluggable*: flip EMBED_PROVIDER / RERANK_PROVIDER /
LLM_PROVIDER to "voyage"/"openrouter" (the production default) for the always-on
hosted service, or to "nomic"/"qwen3"/"ollama" to run the original local
open-source stack on your own machine. No code changes — just configuration.
"""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

load_dotenv()  # populates os.environ from a local .env, if present; no-op otherwise


def _get(key: str, default: str | None = None) -> str | None:
    """Resolve a setting: env var (incl. from .env) → Streamlit secrets → default."""
    if key in os.environ and os.environ[key] != "":
        return os.environ[key]
    try:
        import streamlit as st  # imported lazily; absent in pure-CLI contexts

        if key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        # No secrets file, or Streamlit not installed in this context — ignore.
        pass
    return default


def _ensure_tesseract_on_path() -> None:
    """Make the Tesseract binary discoverable for OCR ingestion (PNG documents).

    pytesseract resolves `tesseract` through PATH only, and the Windows
    installer does not add itself to PATH when run silently — so image
    ingestion fails with TesseractNotFoundError even though it is installed.
    Prepend the install dir for THIS PROCESS only, rather than editing the
    machine's PATH. No-op on Linux (the pod installs tesseract via apt, which
    is already on PATH) and no-op if it is already resolvable.
    """
    import shutil

    if shutil.which("tesseract"):
        return
    candidates = [_get("TESSERACT_DIR")] if _get("TESSERACT_DIR") else []
    candidates += [
        r"C:\Program Files\Tesseract-OCR",
        r"C:\Program Files (x86)\Tesseract-OCR",
        os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR"),
    ]
    for d in candidates:
        if d and os.path.isfile(os.path.join(d, "tesseract.exe")):
            os.environ["PATH"] = d + os.pathsep + os.environ.get("PATH", "")
            return


def _ensure_modern_sqlite() -> None:
    """Swap in pysqlite3 when the stdlib sqlite3 is too old for ChromaDB.

    ChromaDB requires sqlite >= 3.35, but some hosted Linux images (notably
    older Streamlit Community Cloud builds) ship an older system sqlite that
    Python's stdlib module links against — ChromaDB then aborts at import with
    "unsupported version of sqlite3". The standard fix is to import the bundled
    pysqlite3 wheel and alias it over the stdlib name BEFORE chromadb loads.

    Deliberately a no-op when the runtime sqlite is already new enough (every
    current dev machine), so it costs nothing and cannot mask a real problem.
    Must run before `import chromadb`; settings is imported first on every code
    path that reaches the retriever.
    """
    import sqlite3

    if tuple(int(p) for p in sqlite3.sqlite_version.split(".")[:2]) >= (3, 35):
        return
    try:
        __import__("pysqlite3")
        sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
    except ImportError:
        # Nothing more we can do here; chromadb will raise a clear error itself.
        pass


_ensure_tesseract_on_path()
_ensure_modern_sqlite()


# ── Deployment mode ──────────────────────────────────────────────────────────
# "production" → recruiter chat only (the Candidate Setup page is hidden so a
#                recruiter can never edit your profile or trigger ingestion).
# "setup"      → both pages (use this locally when building/updating the profile).
APP_MODE = (_get("APP_MODE", "production") or "production").lower()

# Single shared access code that gates the recruiter chat. Leave empty to disable
# the gate (e.g. while developing locally). Set it via secrets in production.
APP_PASSWORD = _get("APP_PASSWORD", "") or ""


# ── Storage & identity ───────────────────────────────────────────────────────
# Single source of truth for the vector store location and the two collection
# ids. These were previously re-declared as literals in rag/ingest.py,
# rag/retriever.py, agent/tools.py, app_pages/setup.py, evaluation/harness.py and
# the ingestion evaluator — six copies that had to agree or ingestion and
# retrieval would silently address different databases.
CHROMA_PATH = _get("CHROMA_PATH", "./chroma_db") or "./chroma_db"

# The candidate whose profile this deployment serves. Single-candidate app for
# now; the eval harness rebinds agent.tools.CANDIDATE_ID per candidate at runtime
# (see evaluation/pipeline.set_candidate_id), which is why the agent reads it as a
# module attribute rather than importing the value directly.
CANDIDATE_ID = _get("CANDIDATE_ID", "candidate_001") or "candidate_001"
# Separate collection holding the project overview, so recruiters can ask how the
# system itself was built (the search_project tool).
PROJECT_ID = _get("PROJECT_ID", "project_kb") or "project_kb"

# Chunks handed to the answer after reranking. The eval scripts label their runs
# with this too, so it lives here rather than as a literal in each of them.
RETRIEVE_TOP_K = int(_get("RETRIEVE_TOP_K", "8") or "8")


# ── LLM (agent loop, query router, query expansion, build-time summaries) ─────
# "anthropic"  → Claude API directly.
# "openrouter" → any model via OpenRouter's unified API (production default —
#                lets AGENT_MODEL/ROUTER_MODEL name any provider's model).
# "ollama"     → local Ollama model (the original local stack; free for eval).
LLM_PROVIDER = (_get("LLM_PROVIDER", "openrouter") or "openrouter").lower()
ANTHROPIC_API_KEY = _get("ANTHROPIC_API_KEY", "") or ""
OPENROUTER_API_KEY = _get("OPENROUTER_API_KEY", "") or ""

# Model ids are provider-specific (bare "claude-haiku-4-5" for direct Anthropic
# vs. prefixed "anthropic/claude-haiku-4.5" on OpenRouter), so defaults track
# LLM_PROVIDER; override with the AGENT_MODEL/ROUTER_MODEL env vars to pin an
# exact id. OpenRouter can serve both vendors, which is what lets the two roles
# below use different models.
_DEFAULT_AGENT = {
    "anthropic": "claude-haiku-4-5",
    "openrouter": "anthropic/claude-haiku-4.5",
}.get(LLM_PROVIDER, "claude-haiku-4-5")

_DEFAULT_TOOL_SELECT = {
    "anthropic": "claude-haiku-4-5",           # no cheap non-Claude option here
    "openrouter": "google/gemini-2.5-flash-lite",
}.get(LLM_PROVIDER, "claude-haiku-4-5")

# The recruiter-facing answer (synthesis). This is the ONLY user-visible output,
# so it keeps the stronger model: grounding discipline, refusal wording, and
# tone are judged directly by the recruiter.
AGENT_MODEL = _get("AGENT_MODEL", _DEFAULT_AGENT) or _DEFAULT_AGENT

# Retrieval-shaping calls: BROAD/SPECIFIC routing, query expansion, and
# build-time summaries. Cheap per call, but they decide WHICH chunks reach the
# answer — a bad expansion or route silently degrades every downstream metric,
# and unlike tool selection there is no escalation path to recover. Stays on the
# stronger model.
ROUTER_MODEL = _get("ROUTER_MODEL", _DEFAULT_AGENT) or _DEFAULT_AGENT

# Tool selection only (agent/tool_router.score_tools). Isolated on the cheap
# model because it is the single most expensive call — a fixed ~1,300-token
# system prompt re-sent to classify a ~10-token question — and it is the one
# routing decision with a built-in safety net: result-based escalation reruns
# the remaining tools when everything selected comes back empty.
# NOTE: unvalidated against the tool-selection probe. The failure mode to watch
# is the null class — out-of-scope questions need ALL FOUR tools scored low at
# once, and weaker routers tend to fire a tool anyway (a false answer where a
# refusal belongs). collect_tool_scores.analyze() reports this as neg_fire_rate.
TOOL_SELECT_MODEL = _get("TOOL_SELECT_MODEL", _DEFAULT_TOOL_SELECT) or _DEFAULT_TOOL_SELECT
# Local fallback model name when LLM_PROVIDER == "ollama".
OLLAMA_MODEL = _get("OLLAMA_MODEL", "qwen3") or "qwen3"

# ── Tool selection ───────────────────────────────────────────────────────────
# The agent scores every tool 0..1 for a question — an INDEPENDENT per-tool
# relevance probability (see agent/tool_router.py) — then:
#   1. Runs every tool whose score >= TOOL_SELECT_THRESHOLD, concurrently. A low
#      bar (0.30) maximizes recall of the correct tool while still averaging ~1.3
#      tools/question (the scores are confident), and never fires on out-of-scope
#      questions (they score all-low → no tool → refuse).
#   2. RESULT-BASED ESCALATION: if every selected tool comes back empty (no chunks
#      / "Not provided" / skill-not-assessed), run the REMAINING tools concurrently
#      and add their retrieved context — a pay-per-need safety net for the rare
#      case the router missed, instead of pre-firing every tool on every question.
# 0.30 chosen from the tool-score probe (after the improved router prompt): the
# knee at recall 95.5% / ~1.17 tools per question, above the false-refusal zone;
# escalation backstops the residual misses. Tune from the probe or the CSV.
TOOL_SELECT_THRESHOLD = float(_get("TOOL_SELECT_THRESHOLD", "0.30") or "0.30")
TOOL_ESCALATE_ON_EMPTY = (_get("TOOL_ESCALATE_ON_EMPTY", "1") or "1") not in ("0", "false", "False")


# ── Telemetry (per-turn cost / latency / conversation log) ───────────────────
# One record per recruiter question — see agent/telemetry.py. Two sinks: a JSON
# line on stdout (the only one that survives a restart on hosted platforms) and
# an append-only JSONL file that backs the admin view.
TELEMETRY_ENABLED = (_get("TELEMETRY_ENABLED", "1") or "1") not in ("0", "false", "False")
TELEMETRY_LOG_PATH = _get("TELEMETRY_LOG_PATH", "./logs/turns.jsonl") or "./logs/turns.jsonl"

# Gates the hidden admin dashboard at ?admin=<value>. Separate from APP_PASSWORD
# so handing a recruiter the chat code never exposes conversation logs or spend.
# Unset → the dashboard does not exist.
ADMIN_PASSWORD = _get("ADMIN_PASSWORD", "") or ""

# Fallback pricing, USD per million tokens: {model: (input, output)}.
# Only consulted when the provider does not report a cost — OpenRouter does when
# asked, and its number is authoritative. Prices drift, so anything priced from
# this table is flagged `cost_estimated` in the log rather than trusted silently.
MODEL_PRICES_PER_MTOK = {
    "anthropic/claude-haiku-4.5": (1.00, 5.00),
    "google/gemini-2.5-flash-lite": (0.10, 0.40),
    "claude-haiku-4-5": (1.00, 5.00),
}


# ── Embeddings ───────────────────────────────────────────────────────────────
# "voyage" → Voyage AI API (no torch; production default).
# "nomic"  → local nomic-embed via sentence-transformers (original local stack).
EMBED_PROVIDER = (_get("EMBED_PROVIDER", "voyage") or "voyage").lower()
VOYAGE_API_KEY = _get("VOYAGE_API_KEY", "") or ""
VOYAGE_EMBED_MODEL = _get("VOYAGE_EMBED_MODEL", "voyage-3.5-lite") or "voyage-3.5-lite"
NOMIC_EMBED_MODEL = _get("NOMIC_EMBED_MODEL", "nomic-ai/nomic-embed-text-v1.5") \
    or "nomic-ai/nomic-embed-text-v1.5"


# ── Reranker ─────────────────────────────────────────────────────────────────
# "voyage" → Voyage rerank API (no torch; production default).
# "qwen3"  → local Qwen3-Reranker-0.6B (original local stack).
# "none"   → skip reranking, return the fused top-k as-is.
RERANK_PROVIDER = (_get("RERANK_PROVIDER", "voyage") or "voyage").lower()
VOYAGE_RERANK_MODEL = _get("VOYAGE_RERANK_MODEL", "rerank-2.5") or "rerank-2.5"
