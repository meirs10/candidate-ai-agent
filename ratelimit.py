"""
ratelimit.py — Generous per-client throttle for the public recruiter chat.

Purpose: stop a bot flooding the app, not slow a recruiter down. Every question
costs real money (a routing call, up to four tools, embeddings, a reranker call
and a synthesis call), so an unattended script pointed at the chat box is a
billing problem long before it is a load problem.

The limits are deliberately far above human behaviour. A recruiter reads each
answer before asking the next thing; nobody types thirty distinct questions in a
minute. Anyone who hits these limits is not reading.

Design notes:

- Sliding window, not a fixed bucket. A fixed per-minute counter lets a flood of
  2x the limit through by straddling the reset boundary; a sliding window counts
  the actual last 60 seconds.

- Two windows. A short one absorbs bursts, a long one catches the slow drip a
  short window alone never sees — 8 questions a minute, forever, is a bot.

- In-process state, which means per container. This app runs as a single
  process, so that is the whole picture; if it is ever replicated the limit
  becomes per-replica and would need shared state (Redis or the like) to stay
  exact. Said plainly here because an in-memory limiter that silently degrades
  when scaled is a classic way to believe you are protected when you are not.

- State is bounded. Idle clients are evicted, so a long flood from many spoofed
  addresses cannot grow the dict without limit.
"""

from __future__ import annotations

import threading
import time
from collections import deque

import settings as config

_lock = threading.Lock()
_hits: dict[str, deque[float]] = {}

# Only ever prune when the table is actually large, so the common case (a handful
# of visitors) never pays for the scan.
_MAX_TRACKED = 5_000


def _client_key() -> str:
    """Best-effort identity for the caller.

    Behind Streamlit Cloud's proxy the socket address is the proxy's, so the
    forwarded header is the only thing that varies per visitor. It is also
    trivially spoofable by an attacker who is paying attention — which is
    precisely why this is a flood damper and NOT an access control. The access
    decision belongs to the bot check; this only bounds the cost of whoever gets
    through.

    Falls back to the session id so a local run (no proxy, no headers) still
    limits per browser session rather than lumping everyone under one key.
    """
    try:
        import streamlit as st

        headers = getattr(st.context, "headers", None) or {}
        forwarded = headers.get("X-Forwarded-For") or headers.get("x-forwarded-for")
        if forwarded:
            # First entry is the original client; the rest are proxies.
            return forwarded.split(",")[0].strip()
        real_ip = headers.get("X-Real-Ip") or headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
        sid = st.session_state.get("session_id")
        if sid:
            return f"session:{sid}"
    except Exception:
        pass
    return "unknown"


def _prune(now: float, longest: int) -> None:
    """Drop clients with no activity inside the longest window. Caller holds the lock."""
    if len(_hits) <= _MAX_TRACKED:
        return
    cutoff = now - longest
    for key in [k for k, dq in _hits.items() if not dq or dq[-1] < cutoff]:
        del _hits[key]


def check(key: str | None = None) -> tuple[bool, int]:
    """Record an attempt and report whether it is allowed.

    Returns (allowed, retry_after_seconds). retry_after is 0 when allowed, and
    otherwise the whole seconds until the offending window has room again.

    A blocked attempt is NOT recorded. Otherwise a bot hammering the endpoint
    keeps its own window permanently full and extends its block indefinitely,
    which turns a throttle into a ban — and would do the same to a real person
    who shares an office IP with whoever tripped it.
    """
    if not config.RATE_LIMIT_ENABLED:
        return True, 0

    windows = (
        (config.RATE_LIMIT_PER_MINUTE, 60),
        (config.RATE_LIMIT_PER_HOUR, 3600),
    )
    longest = max(span for _, span in windows)
    key = key or _client_key()
    now = time.monotonic()

    with _lock:
        dq = _hits.setdefault(key, deque())
        while dq and dq[0] <= now - longest:
            dq.popleft()

        for limit, span in windows:
            if limit <= 0:
                continue
            start = now - span
            used = sum(1 for t in dq if t > start)
            if used >= limit:
                oldest = next(t for t in dq if t > start)
                return False, max(1, int(oldest + span - now) + 1)

        dq.append(now)
        _prune(now, longest)

    return True, 0


def reset() -> None:
    """Clear all state. Tests only."""
    with _lock:
        _hits.clear()
