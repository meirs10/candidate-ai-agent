"""
telemetry.py — Per-turn observability for the recruiter chat.

Records one structured record per recruiter question: what was asked, what was
answered, which tools fired and with what confidence, how the query was routed,
every LLM call it took (role, model, tokens, cost, latency), and the wall-clock
time. That is enough to answer "what is this costing me, where is the money
going, and what are recruiters actually asking?" without a tracing backend.

Two sinks, deliberately:

  stdout  One JSON line per turn. This is what Streamlit Community Cloud shows in
          its log viewer, and it is the ONLY sink that survives a container
          restart — the hosted filesystem is ephemeral.
  file    logs/turns.jsonl, append-only. Backs the admin view and local analysis.
          Lost on redeploy when hosted; durable when running locally.

Collection is passive: if anything here raises, the recruiter still gets their
answer. Observability must never be able to take down the thing it observes.

Concurrency
-----------
The agent runs its tools in a ThreadPoolExecutor, and retrieval makes its own LLM
calls (query expansion, BROAD/SPECIFIC routing) *inside* those worker threads. A
thread-local would silently drop them. A ContextVar propagated with
contextvars.copy_context() at submit time reaches the workers correctly, which is
why agent._run_tools_concurrently submits through a copied context.
"""

from __future__ import annotations

import json
import os
import threading
import time
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field, fields, asdict

import settings as config

# The turn currently being recorded, visible to every LLM call it triggers —
# including ones made from tool worker threads (see module docstring).
_current_turn: ContextVar["TurnRecord | None"] = ContextVar("_current_turn", default=None)

_file_lock = threading.Lock()


@dataclass
class LLMCall:
    """One completion request. `role` is which of the three configured model
    roles paid for it, which is what makes the cost breakdown actionable."""
    role: str                      # synthesis | router | tool_select
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    # True when cost came from a local price table rather than the provider,
    # so a stale table is visible in the data instead of quietly wrong.
    cost_estimated: bool = False


@dataclass
class TurnRecord:
    turn_id: str
    session_id: str
    ts: str
    question: str
    answer: str = ""
    tools_selected: list = field(default_factory=list)
    tool_scores: dict = field(default_factory=dict)
    route: str | None = None
    n_chunks: int = 0
    escalated: bool = False
    llm_calls: list = field(default_factory=list)
    latency_ms: int = 0
    error: str | None = None

    # Guards llm_calls against concurrent appends from tool worker threads.
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def add_call(self, call: LLMCall) -> None:
        with self._lock:
            self.llm_calls.append(call)

    @property
    def total_cost_usd(self) -> float:
        return round(sum(c.cost_usd for c in self.llm_calls), 6)

    @property
    def total_tokens(self) -> int:
        return sum(c.prompt_tokens + c.completion_tokens for c in self.llm_calls)

    def to_dict(self) -> dict:
        # Field-by-field, not dataclasses.asdict(): asdict() recurses and tries to
        # deep-copy every value, which fails on the threading.Lock below.
        d = {f.name: getattr(self, f.name) for f in fields(self) if f.name != "_lock"}
        d["llm_calls"] = [asdict(c) for c in self.llm_calls]
        d["n_llm_calls"] = len(self.llm_calls)
        d["total_cost_usd"] = self.total_cost_usd
        d["total_tokens"] = self.total_tokens
        # Cost split by model role — the number worth watching month to month.
        by_role: dict[str, float] = {}
        for c in self.llm_calls:
            by_role[c.role] = round(by_role.get(c.role, 0.0) + c.cost_usd, 6)
        d["cost_by_role"] = by_role
        return d


# ── Cost ─────────────────────────────────────────────────────────────────────

def estimate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Fallback pricing when the provider did not return a cost.

    OpenRouter reports the real charge when asked (see llm._complete_openrouter),
    and that is always preferred — prices change and a hardcoded table goes stale
    silently. This exists so a turn still carries a usable number if that field
    is missing, and calls priced this way are flagged `cost_estimated`.
    """
    prices = config.MODEL_PRICES_PER_MTOK.get(model)
    if not prices:
        return 0.0
    return round(prompt_tokens / 1e6 * prices[0] + completion_tokens / 1e6 * prices[1], 8)


def record_llm_call(role: str, model: str, prompt_tokens: int, completion_tokens: int,
                    cost_usd: float | None, latency_ms: int) -> None:
    """Attach one LLM call to the turn in scope. No-op outside a turn (the eval
    harness and CLI tools call the same LLM client and should not be charged to a
    recruiter conversation)."""
    turn = _current_turn.get()
    if turn is None:
        return
    estimated = cost_usd is None
    if estimated:
        cost_usd = estimate_cost(model, prompt_tokens, completion_tokens)
    turn.add_call(LLMCall(
        role=role, model=model,
        prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
        cost_usd=cost_usd or 0.0, latency_ms=latency_ms, cost_estimated=estimated,
    ))


# ── Turn lifecycle ───────────────────────────────────────────────────────────

@contextmanager
def turn(question: str, session_id: str = "local"):
    """Open a recording scope for one recruiter question.

    Yields the TurnRecord so the caller can fill in what only it knows (tools,
    route, answer). The record is written on exit — including on exception, so a
    failed turn is still visible with its error and its already-incurred cost.
    """
    if not config.TELEMETRY_ENABLED:
        yield None
        return

    rec = TurnRecord(
        turn_id=uuid.uuid4().hex[:12],
        session_id=session_id,
        ts=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        question=question,
    )
    token = _current_turn.set(rec)
    started = time.perf_counter()
    try:
        yield rec
    except Exception as e:
        rec.error = f"{type(e).__name__}: {e}"
        raise
    finally:
        rec.latency_ms = int((time.perf_counter() - started) * 1000)
        _current_turn.reset(token)
        _emit(rec)


def current_turn() -> "TurnRecord | None":
    return _current_turn.get()


# ── Sinks ────────────────────────────────────────────────────────────────────

def _emit(rec: TurnRecord) -> None:
    """Write the record to both sinks. Never raises."""
    try:
        payload = rec.to_dict()
    except Exception as e:                                  # pragma: no cover
        print(f"[Telemetry] could not serialize turn: {e}")
        return

    line = json.dumps(payload, ensure_ascii=False)

    # 1. stdout — the durable sink on hosted platforms.
    try:
        print("[turn] " + line, flush=True)
    except Exception:
        pass

    # 2. append-only file — backs the admin view.
    try:
        path = config.TELEMETRY_LOG_PATH
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with _file_lock, open(path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception as e:
        print(f"[Telemetry] could not write {config.TELEMETRY_LOG_PATH}: {e}")


def read_turns(limit: int | None = None) -> list[dict]:
    """Load recorded turns, newest last. Skips malformed lines rather than
    failing the whole view — a truncated final write must not hide the history."""
    path = config.TELEMETRY_LOG_PATH
    if not os.path.exists(path):
        return []
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows[-limit:] if limit else rows
