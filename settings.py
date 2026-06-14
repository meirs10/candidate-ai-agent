"""
config.py — Single source of truth for runtime configuration.

Everything (LLM provider, embeddings provider, reranker provider, API keys, the
deployment mode, and the recruiter access code) is resolved here, in this order:

    1. Environment variable        (best for CI, the eval harness, local shells)
    2. Streamlit secrets           (best for Streamlit Community Cloud / HF Spaces)
    3. Hard-coded default          (Option A: all-API, production-safe)

This is what makes the project *pluggable*: flip EMBED_PROVIDER / RERANK_PROVIDER /
LLM_PROVIDER to "voyage"/"anthropic" (the production default) for the always-on
hosted service, or to "nomic"/"qwen3"/"ollama" to run the original local
open-source stack on your own machine. No code changes — just configuration.
"""

from __future__ import annotations

import os


def _get(key: str, default: str | None = None) -> str | None:
    """Resolve a setting: env var → Streamlit secrets → default."""
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
LLM_PROVIDER = (_get("LLM_PROVIDER", "anthropic") or "anthropic").lower()
ANTHROPIC_API_KEY = _get("ANTHROPIC_API_KEY", "") or ""

# The agent that answers recruiters. Start on Haiku (fast + cheap); bump to
# claude-sonnet-4-6 if you want richer answers.
AGENT_MODEL = _get("AGENT_MODEL", "claude-haiku-4-5") or "claude-haiku-4-5"
# Auxiliary single-shot calls (BROAD/SPECIFIC routing, query expansion, summaries).
ROUTER_MODEL = _get("ROUTER_MODEL", "claude-haiku-4-5") or "claude-haiku-4-5"
# Local fallback model name when LLM_PROVIDER == "ollama".
OLLAMA_MODEL = _get("OLLAMA_MODEL", "qwen3") or "qwen3"


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
