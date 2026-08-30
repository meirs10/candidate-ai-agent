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


# ── Deployment mode ──────────────────────────────────────────────────────────
# "production" → recruiter chat only (the Candidate Setup page is hidden so a
#                recruiter can never edit your profile or trigger ingestion).
# "setup"      → both pages (use this locally when building/updating the profile).
APP_MODE = (_get("APP_MODE", "production") or "production").lower()

# Single shared access code that gates the recruiter chat. Leave empty to disable
# the gate (e.g. while developing locally). Set it via secrets in production.
APP_PASSWORD = _get("APP_PASSWORD", "") or ""


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

_DEFAULT_ROUTER = {
    "anthropic": "claude-haiku-4-5",           # no cheap non-Claude option here
    "openrouter": "google/gemini-2.5-flash-lite",
}.get(LLM_PROVIDER, "claude-haiku-4-5")

# The recruiter-facing answer (synthesis). This is the ONLY user-visible output,
# so it keeps the stronger model: grounding discipline, refusal wording, and
# tone are judged directly by the recruiter.
AGENT_MODEL = _get("AGENT_MODEL", _DEFAULT_AGENT) or _DEFAULT_AGENT

# Everything else: tool-selection scoring, BROAD/SPECIFIC routing, query
# expansion, build-time summaries. Invisible plumbing judged only by whether it
# picked right — ~68% of per-turn spend on work the recruiter never sees.
# Gemini 2.5 Flash Lite is ~10x cheaper than Haiku ($0.10/$0.40 vs $1/$5) and
# well above the 8B-class local model this pipeline was originally tuned on.
# NOTE: unvalidated against the tool-selection probe. The failure mode to watch
# is the null class — out-of-scope questions need ALL FOUR tools scored low at
# once, and weaker routers tend to fire a tool anyway (a false answer where a
# refusal belongs). collect_tool_scores.analyze() reports this as neg_fire_rate.
ROUTER_MODEL = _get("ROUTER_MODEL", _DEFAULT_ROUTER) or _DEFAULT_ROUTER
# Local fallback model name when LLM_PROVIDER == "ollama".
OLLAMA_MODEL = _get("OLLAMA_MODEL", "qwen3") or "qwen3"

# ── Tool selection ───────────────────────────────────────────────────────────
# The agent scores every tool 0..1 for a question — an INDEPENDENT per-tool
# relevance probability (see agent/tool_router.py) — then:
#   1. Runs every tool whose score >= TOOL_SELECT_THRESHOLD, concurrently. A low
#      bar (0.20) maximizes recall of the correct tool while still averaging ~1.3
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


def using_local_models() -> bool:
    """True when any heavyweight local (torch) model is selected."""
    return (
        EMBED_PROVIDER == "nomic"
        or RERANK_PROVIDER == "qwen3"
        or LLM_PROVIDER == "ollama"
    )
