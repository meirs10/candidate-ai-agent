"""
llm.py — Provider-pluggable LLM client.

Exposes one provider-neutral interface used by the agent and the retrieval
helpers, with three backends selected via config.LLM_PROVIDER:

    "openrouter" → any model via OpenRouter's unified API (production default)
    "anthropic"  → Claude API directly (no local model server)
    "ollama"     → local Ollama model (the original local stack; free for eval)

The surface is deliberately one method: complete(prompt, system, max_tokens,
model) → str. The agent is single-pass — the router scores all tools in one call,
the selected tools run concurrently, and one synthesis call answers from their
combined output — so no provider ever needs a native tool-calling loop. Tool
descriptions live in agent/tool_router.ROUTER_SYSTEM, not in a provider schema.

`model` selects which of the three configured roles this call bills to
(AGENT_MODEL / ROUTER_MODEL / TOOL_SELECT_MODEL); see settings.py.
"""

from __future__ import annotations

import json
import re
import time

# Imported as `config` for readability, but the module is named `settings` so it
# can't shadow the skill scorer's own flat `import config`.
import settings as config
from agent import telemetry

# Max generation tokens — high enough for a full recruiter answer, low enough to
# stay well under any HTTP timeout without streaming.
AGENT_MAX_TOKENS = 1024   # recruiter-facing synthesis (agent/agent.py:_synthesize)
COMPLETE_MAX_TOKENS = 512  # routing / expansion / summaries

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)

# One pooled, retrying Session shared by every OpenRouter call. The eval harness
# scores tools concurrently, and bare requests.post has no retry: transient
# connection resets under concurrency would abort a whole run. (The Anthropic SDK
# does this internally; the REST backend has to do it explicitly.)
_SESSION = None


def _openrouter_session():
    global _SESSION
    if _SESSION is None:
        import requests
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry

        retry = Retry(
            total=5,
            connect=5,
            read=5,
            backoff_factor=0.8,          # 0.8s, 1.6s, 3.2s, 6.4s, 12.8s
            status_forcelist=(408, 409, 429, 500, 502, 503, 504),
            allowed_methods=frozenset(["POST"]),  # POST is not retried by default
            raise_on_status=False,
        )
        session = requests.Session()
        adapter = HTTPAdapter(max_retries=retry, pool_connections=16, pool_maxsize=16)
        session.mount("https://", adapter)
        _SESSION = session
    return _SESSION


class LLMClient:
    """One client, two backends. Instantiated once and shared."""

    def __init__(self):
        self.provider = config.LLM_PROVIDER
        self.agent_model = config.AGENT_MODEL
        self.router_model = config.ROUTER_MODEL
        self._anthropic = None  # lazy

    # -- Anthropic client (lazy) --------------------------------------------
    def _client(self):
        if self._anthropic is None:
            import anthropic

            self._anthropic = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY or None)
        return self._anthropic

    # -- Single-shot completion (router, query expansion, summaries) --------
    def complete(self, prompt: str, system: str | None = None,
                 max_tokens: int = COMPLETE_MAX_TOKENS, model: str | None = None,
                 role: str = "router") -> str:
        """model defaults to router_model (most complete() call sites are
        routing/query-expansion); pass model=self.agent_model explicitly for the
        recruiter-facing synthesis call.

        `role` labels the call in telemetry. It cannot be derived from the model
        id: AGENT_MODEL and ROUTER_MODEL are the same model by default, so the
        cost breakdown would collapse two roles into one. Callers state it."""
        model = model or self.router_model

        if self.provider == "ollama":
            import ollama

            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            started = time.perf_counter()
            # NOTE: `model` is intentionally ignored here. Under Ollama there is
            # one local model, so the three roles all resolve to OLLAMA_MODEL —
            # the role split exists to control spend, and local inference is free.
            resp = ollama.chat(model=config.OLLAMA_MODEL, messages=messages, options={"num_predict": 4096})
            telemetry.record_llm_call(
                role=role, model=config.OLLAMA_MODEL,
                prompt_tokens=resp.get("prompt_eval_count", 0) or 0,
                completion_tokens=resp.get("eval_count", 0) or 0,
                cost_usd=0.0,  # local inference: free by construction
                latency_ms=int((time.perf_counter() - started) * 1000),
            )
            return _THINK_RE.sub("", resp["message"]["content"]).strip()

        if self.provider == "openrouter":
            return self._complete_openrouter(prompt, system, max_tokens, model, role)

        # Anthropic
        kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system
        started = time.perf_counter()
        resp = self._client().messages.create(**kwargs)
        telemetry.record_llm_call(
            role=role, model=model,
            prompt_tokens=getattr(resp.usage, "input_tokens", 0),
            completion_tokens=getattr(resp.usage, "output_tokens", 0),
            cost_usd=None,  # the SDK reports tokens, not cost — price locally
            latency_ms=int((time.perf_counter() - started) * 1000),
        )
        return "".join(b.text for b in resp.content if b.type == "text").strip()

    # -- OpenRouter backend (OpenAI-compatible REST) --------------------------
    def _complete_openrouter(self, prompt: str, system: str | None,
                              max_tokens: int, model: str, role: str) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        started = time.perf_counter()
        resp = _openrouter_session().post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
                "X-Title": "candidate-ai-agent",
            },
            json={
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                # Ask OpenRouter to return what this call actually cost. Without
                # it we would have to price calls from a hardcoded table that
                # goes stale silently; with it, telemetry reports the real charge.
                "usage": {"include": True},
            },
            timeout=90,
        )
        latency_ms = int((time.perf_counter() - started) * 1000)
        resp.raise_for_status()
        body = resp.json()
        # OpenRouter can return HTTP 200 with an error payload (upstream refusal,
        # provider outage) — surface it rather than KeyError-ing on "choices".
        if "choices" not in body:
            raise RuntimeError(f"OpenRouter error: {body.get('error') or body}")

        usage = body.get("usage") or {}
        telemetry.record_llm_call(
            role=role,
            model=model,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            # None → telemetry falls back to the local price table and flags it.
            cost_usd=usage.get("cost"),
            latency_ms=latency_ms,
        )

        content = body["choices"][0]["message"].get("content") or ""
        return _THINK_RE.sub("", content).strip()

    # ── Streaming ────────────────────────────────────────────────────────────

    def complete_stream(self, prompt: str, system: str | None = None,
                        max_tokens: int = COMPLETE_MAX_TOKENS,
                        model: str | None = None, role: str = "agent"):
        """Yield the completion in fragments as the model produces them.

        Used for the recruiter-facing answer only. Everything else — routing,
        expansion, summaries — is machine-read, so streaming it would buy
        nothing.

        This is real streaming rather than typing out an already-finished string.
        The distinction matters: simulated typing can only start once the whole
        answer exists, so it ADDS its own duration to a wait the recruiter has
        already served. Streaming spends that same time showing words.

        Providers that cannot stream fall back to yielding the finished text in
        one piece, so callers never need to branch.
        """
        if self.provider == "openrouter":
            yield from self._stream_openrouter(prompt, system, max_tokens,
                                               model or config.AGENT_MODEL, role)
            return
        if self.provider == "ollama":
            yield from self._stream_ollama(prompt, system, role)
            return
        yield self.complete(prompt, system=system, max_tokens=max_tokens,
                            model=model, role=role)

    def _stream_openrouter(self, prompt: str, system: str | None,
                           max_tokens: int, model: str, role: str):
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        started = time.perf_counter()
        usage: dict = {}
        buffered = ""

        with _openrouter_session().post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
                "X-Title": "candidate-ai-agent",
            },
            json={
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "stream": True,
                # The usage block arrives in a final chunk after the content,
                # so cost accounting survives streaming unchanged.
                "usage": {"include": True},
            },
            timeout=90,
            stream=True,
        ) as resp:
            resp.raise_for_status()
            # Decode explicitly rather than with iter_lines(decode_unicode=True).
            # That flag decodes using resp.encoding, and requests defaults a
            # text/event-stream with no declared charset to ISO-8859-1 — so an
            # em-dash arrived as "â" plus two invisible bytes and answers came
            # out visibly corrupted. SSE frames are newline-delimited and the
            # payload is JSON on a single line, so no multi-byte character can
            # straddle a line boundary; decoding each line as UTF-8 is safe.
            for line in resp.iter_lines(decode_unicode=False):
                if not line:
                    continue
                raw = line.decode("utf-8", errors="replace")
                if not raw.startswith("data: "):
                    continue          # keep-alive comments and blank separators
                payload = raw[6:]
                if payload == "[DONE]":
                    break
                try:
                    event = json.loads(payload)
                except json.JSONDecodeError:
                    continue
                if event.get("usage"):
                    usage = event["usage"]
                choices = event.get("choices") or []
                if not choices:
                    continue
                piece = (choices[0].get("delta") or {}).get("content") or ""
                if piece:
                    buffered += piece
                    yield piece

        telemetry.record_llm_call(
            role=role,
            model=model,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            cost_usd=usage.get("cost"),
            latency_ms=int((time.perf_counter() - started) * 1000),
        )

    def _stream_ollama(self, prompt: str, system: str | None, role: str):
        import ollama

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        started = time.perf_counter()
        prompt_tokens = completion_tokens = 0
        for chunk in ollama.chat(model=config.OLLAMA_MODEL, messages=messages,
                                 stream=True, options={"num_predict": 4096}):
            piece = (chunk.get("message") or {}).get("content") or ""
            if piece:
                yield piece
            if chunk.get("done"):
                prompt_tokens = chunk.get("prompt_eval_count", 0) or 0
                completion_tokens = chunk.get("eval_count", 0) or 0

        telemetry.record_llm_call(
            role=role,
            model=config.OLLAMA_MODEL,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost_usd=0.0,          # local model, no charge
            latency_ms=int((time.perf_counter() - started) * 1000),
        )
