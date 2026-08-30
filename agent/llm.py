"""
llm.py — Provider-pluggable LLM client.

Exposes one provider-neutral interface used by the agent loop and the retrieval
helpers, with three backends selected via config.LLM_PROVIDER:

    "openrouter" → any model via OpenRouter's unified API (production default)
    "anthropic"  → Claude API directly (no local model server)
    "ollama"     → local Ollama model (the original local stack; free for eval)

Neutral message format (what callers build):
    {"role": "user",      "content": str}
    {"role": "assistant", "content": str, "tool_calls": [ToolCall, ...]}   # tool_calls optional
    {"role": "tool",      "tool_call_id": str, "content": str}

Neutral tool format (see agent/tools.py):
    {"name": str, "description": str, "parameters": {<JSON schema>}}

ToolCall: {"id": str, "name": str, "arguments": dict}

chat() returns a Reply(text, tool_calls, stop_reason); complete() returns a str.
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field

# Imported as `config` for readability, but the module is named `settings` so it
# can't shadow the skill scorer's own flat `import config`.
import settings as config

# Max generation tokens — high enough for a full recruiter answer, low enough to
# stay well under any HTTP timeout without streaming.
AGENT_MAX_TOKENS = 1024
COMPLETE_MAX_TOKENS = 512

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


@dataclass
class Reply:
    text: str
    tool_calls: list[dict] = field(default_factory=list)
    stop_reason: str | None = None


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
                 max_tokens: int = COMPLETE_MAX_TOKENS, model: str | None = None) -> str:
        """model defaults to router_model (the caller for most complete() call
        sites — routing/query-expansion/tool-scoring); pass model=self.agent_model
        explicitly for the recruiter-facing synthesis call."""
        model = model or self.router_model

        if self.provider == "ollama":
            import ollama

            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            resp = ollama.chat(model=config.OLLAMA_MODEL, messages=messages, options={"num_predict": 4096})
            return _THINK_RE.sub("", resp["message"]["content"]).strip()

        if self.provider == "openrouter":
            return self._complete_openrouter(prompt, system, max_tokens, model)

        # Anthropic
        kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system
        resp = self._client().messages.create(**kwargs)
        return "".join(b.text for b in resp.content if b.type == "text").strip()

    # -- OpenRouter backend (OpenAI-compatible REST) --------------------------
    def _complete_openrouter(self, prompt: str, system: str | None,
                              max_tokens: int, model: str) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        resp = _openrouter_session().post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
                "X-Title": "candidate-ai-agent",
            },
            json={"model": model, "messages": messages, "max_tokens": max_tokens},
            timeout=90,
        )
        resp.raise_for_status()
        body = resp.json()
        # OpenRouter can return HTTP 200 with an error payload (upstream refusal,
        # provider outage) — surface it rather than KeyError-ing on "choices".
        if "choices" not in body:
            raise RuntimeError(f"OpenRouter error: {body.get('error') or body}")
        content = body["choices"][0]["message"].get("content") or ""
        return _THINK_RE.sub("", content).strip()

    # -- Tool-calling chat (the agent loop) ---------------------------------
    def chat(self, system: str, messages: list[dict],
             tools: list[dict] | None = None,
             max_tokens: int = AGENT_MAX_TOKENS) -> Reply:
        if self.provider == "ollama":
            return self._chat_ollama(system, messages, tools)
        if self.provider == "openrouter":
            # Unused: the agent is single-pass (score_tools + complete()), so no
            # caller needs a tool-calling loop. Fail loudly rather than silently
            # falling through to the Anthropic client, which would send an
            # OpenRouter-style model id ("anthropic/claude-haiku-4.5") to
            # api.anthropic.com and demand an ANTHROPIC_API_KEY.
            raise NotImplementedError(
                "LLMClient.chat() has no OpenRouter backend. The agent uses "
                "complete() only; add a tool-calling backend here if that changes."
            )
        return self._chat_anthropic(system, messages, tools, max_tokens)

    # -- Anthropic backend ---------------------------------------------------
    def _chat_anthropic(self, system, messages, tools, max_tokens) -> Reply:
        kwargs = {
            "model": self.agent_model,
            "max_tokens": max_tokens,
            "messages": _to_anthropic_messages(messages),
        }
        if system:
            # cache_control caches the (frozen) system prompt + tool schemas so
            # every turn after the first pays ~0.1x on that prefix.
            kwargs["system"] = [
                {"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}
            ]
        if tools:
            kwargs["tools"] = [
                {"name": t["name"], "description": t["description"],
                 "input_schema": t["parameters"]}
                for t in tools
            ]
        resp = self._client().messages.create(**kwargs)
        text = "".join(b.text for b in resp.content if b.type == "text").strip()
        tool_calls = [
            {"id": b.id, "name": b.name, "arguments": b.input}
            for b in resp.content if b.type == "tool_use"
        ]
        return Reply(text=text, tool_calls=tool_calls, stop_reason=resp.stop_reason)

    # -- Ollama backend ------------------------------------------------------
    def _chat_ollama(self, system, messages, tools) -> Reply:
        import ollama

        oll_messages = []
        if system:
            oll_messages.append({"role": "system", "content": system})
        for m in messages:
            role = m["role"]
            if role == "tool":
                oll_messages.append({"role": "tool", "content": m["content"]})
            elif role == "assistant" and m.get("tool_calls"):
                oll_messages.append({
                    "role": "assistant",
                    "content": m.get("content", ""),
                    "tool_calls": [
                        {"function": {"name": tc["name"], "arguments": tc["arguments"]}}
                        for tc in m["tool_calls"]
                    ],
                })
            else:
                oll_messages.append({"role": role, "content": m.get("content", "")})

        kwargs = {"model": config.OLLAMA_MODEL, "messages": oll_messages,
                  "options": {"num_predict": 2048}}
        if tools:
            kwargs["tools"] = [
                {"type": "function", "function": {
                    "name": t["name"], "description": t["description"],
                    "parameters": t["parameters"]}}
                for t in tools
            ]
        resp = ollama.chat(**kwargs)
        message = resp["message"]
        tool_calls = [
            {"id": tc.get("id") or uuid.uuid4().hex,
             "name": tc["function"]["name"],
             "arguments": tc["function"]["arguments"]}
            for tc in (message.get("tool_calls") or [])
        ]
        text = _THINK_RE.sub("", message.get("content") or "").strip()
        return Reply(text=text, tool_calls=tool_calls)


# -- Neutral → Anthropic message conversion ---------------------------------

def _to_anthropic_messages(messages: list[dict]) -> list[dict]:
    """Convert neutral messages into Anthropic's content-block format.

    Assistant tool calls become `tool_use` blocks; `tool` results are grouped
    into the following `user` turn as `tool_result` blocks (Anthropic requires a
    tool_use turn to be answered by tool_result blocks in the next user turn).
    """
    out: list[dict] = []
    for m in messages:
        role = m["role"]
        if role == "user":
            out.append({"role": "user", "content": m["content"]})
        elif role == "assistant":
            blocks = []
            if m.get("content"):
                blocks.append({"type": "text", "text": m["content"]})
            for tc in m.get("tool_calls", []):
                blocks.append({
                    "type": "tool_use", "id": tc["id"],
                    "name": tc["name"], "input": tc["arguments"],
                })
            out.append({"role": "assistant", "content": blocks or ""})
        elif role == "tool":
            block = {
                "type": "tool_result",
                "tool_use_id": m["tool_call_id"],
                "content": m["content"],
            }
            # Attach to the open tool-result user turn, or start a new one.
            if out and out[-1]["role"] == "user" and isinstance(out[-1]["content"], list):
                out[-1]["content"].append(block)
            else:
                out.append({"role": "user", "content": [block]})
    return out
