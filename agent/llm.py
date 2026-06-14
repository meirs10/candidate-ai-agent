"""
llm.py — Provider-pluggable LLM client.

Exposes one provider-neutral interface used by the agent loop and the retrieval
helpers, with two backends selected via config.LLM_PROVIDER:

    "anthropic" → Claude API (production default; always-on, no local model server)
    "ollama"    → local Ollama model (the original local stack; free for eval)

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

import config

# Max generation tokens — high enough for a full recruiter answer, low enough to
# stay well under any HTTP timeout without streaming.
AGENT_MAX_TOKENS = 1024
COMPLETE_MAX_TOKENS = 512

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


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
                 max_tokens: int = COMPLETE_MAX_TOKENS) -> str:
        if self.provider == "ollama":
            import ollama

            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            resp = ollama.chat(model=config.OLLAMA_MODEL, messages=messages)
            return _THINK_RE.sub("", resp["message"]["content"]).strip()

        # Anthropic
        kwargs = {
            "model": self.router_model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system
        resp = self._client().messages.create(**kwargs)
        return "".join(b.text for b in resp.content if b.type == "text").strip()

    # -- Tool-calling chat (the agent loop) ---------------------------------
    def chat(self, system: str, messages: list[dict],
             tools: list[dict] | None = None,
             max_tokens: int = AGENT_MAX_TOKENS) -> Reply:
        if self.provider == "ollama":
            return self._chat_ollama(system, messages, tools)
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
