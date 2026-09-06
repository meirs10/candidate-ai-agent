"""
admin.py — Private dashboard over the conversation log.

Spend, latency, and every recruiter conversation the deployed agent has handled.

Access: reachable ONLY at ?admin=<ADMIN_PASSWORD>, and never listed in the
sidebar. main.py registers this page only when that query parameter matches, so a
recruiter holding the chat access code has no way to discover it exists. The
secret is deliberately separate from APP_PASSWORD — handing out the chat link
must never expose what people asked or what it cost.
"""

import json

import pandas as pd
import streamlit as st

import settings as config
from agent.telemetry import read_turns
from app_pages import ui

ui.inject_css()
# The reading measure that suits chat answers is too narrow for tables of turns
# and per-model cost breakdowns. Streamlit's "centered" layout is just a
# max-width on .block-container, so widening it here is enough — no need to make
# every page wide for the sake of this one.
st.markdown(
    "<style>.block-container{max-width:1200px !important;}</style>",
    unsafe_allow_html=True,
)
ui.header(
    "Usage & Conversations",
    "What the deployed agent has been asked, and what it cost",
    monogram="📊", badge="private",
)
st.write("")

rows = read_turns()
if not rows:
    st.info(
        f"No turns recorded yet at `{config.TELEMETRY_LOG_PATH}`.\n\n"
        "On Streamlit Community Cloud this file is **ephemeral** — it resets on "
        "every redeploy or sleep. The durable copy is the `[turn]` JSON line each "
        "conversation writes to stdout, visible in the platform's log viewer."
    )
    st.stop()

df = pd.DataFrame(rows)
for col, default in (("total_cost_usd", 0.0), ("latency_ms", 0), ("total_tokens", 0),
                     ("n_llm_calls", 0)):
    if col not in df.columns:
        df[col] = default

# ── Headline numbers ─────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Conversations", df["session_id"].nunique())
c2.metric("Turns", len(df))
c3.metric("Total spend", f"${df['total_cost_usd'].sum():.4f}")
c4.metric("Avg / turn", f"${df['total_cost_usd'].mean():.5f}")

c1, c2, c3, c4 = st.columns(4)
# p95 alongside the median: the median hides the slow tail a recruiter actually
# notices, and cold starts + escalation make that tail real.
c1.metric("Median latency", f"{df['latency_ms'].median()/1000:.1f}s")
c2.metric("p95 latency", f"{df['latency_ms'].quantile(0.95)/1000:.1f}s")
c3.metric("Avg tokens / turn", f"{df['total_tokens'].mean():.0f}")
c4.metric("Errors", int(df["error"].notna().sum()) if "error" in df else 0)

st.divider()

# ── Where the money goes ─────────────────────────────────────────────────────
st.subheader("Cost breakdown")

calls = [dict(c, turn_id=r.get("turn_id")) for r in rows for c in (r.get("llm_calls") or [])]
if calls:
    cdf = pd.DataFrame(calls)
    left, right = st.columns(2)
    with left:
        st.caption("By model role")
        by_role = cdf.groupby("role").agg(
            calls=("model", "size"),
            cost_usd=("cost_usd", "sum"),
            avg_latency_ms=("latency_ms", "mean"),
        ).sort_values("cost_usd", ascending=False)
        by_role["cost_pct"] = (by_role["cost_usd"] / by_role["cost_usd"].sum() * 100).round(1)
        st.dataframe(by_role.round(6), use_container_width=True)
    with right:
        st.caption("By model")
        by_model = cdf.groupby("model").agg(
            calls=("role", "size"),
            prompt_tokens=("prompt_tokens", "sum"),
            completion_tokens=("completion_tokens", "sum"),
            cost_usd=("cost_usd", "sum"),
        ).sort_values("cost_usd", ascending=False)
        st.dataframe(by_model.round(6), use_container_width=True)

    if cdf["cost_estimated"].any():
        n = int(cdf["cost_estimated"].sum())
        st.caption(
            f"{n} of {len(cdf)} calls were priced from the local table in "
            "settings.MODEL_PRICES_PER_MTOK because the provider returned no cost. "
            "Those figures can drift from the real charge."
        )

st.divider()

# ── Conversations ────────────────────────────────────────────────────────────
st.subheader("Conversations")

q = st.text_input("Search questions and answers", placeholder="e.g. Python, salary, PPO")
view = df.copy()
if q:
    needle = q.lower()
    view = view[view.apply(
        lambda r: needle in str(r.get("question", "")).lower()
                  or needle in str(r.get("answer", "")).lower(), axis=1)]
    st.caption(f"{len(view)} of {len(df)} turns match.")

cols = [c for c in ("ts", "session_id", "question", "answer", "tools_selected",
                    "route", "n_chunks", "escalated", "total_cost_usd",
                    "latency_ms", "error") if c in view.columns]
st.dataframe(
    view[cols].iloc[::-1],          # newest first
    use_container_width=True, height=420,
)

with st.expander("Inspect a single turn"):
    if len(view):
        ids = list(view["turn_id"].iloc[::-1]) if "turn_id" in view else []
        if ids:
            picked = st.selectbox("Turn", ids)
            match = next((r for r in rows if r.get("turn_id") == picked), None)
            if match:
                st.json(match)

st.download_button(
    "Download log (CSV)",
    data=view[cols].to_csv(index=False).encode("utf-8"),
    file_name="conversations.csv",
    mime="text/csv",
)
st.download_button(
    "Download log (JSONL)",
    data="\n".join(json.dumps(r, ensure_ascii=False) for r in rows).encode("utf-8"),
    file_name="turns.jsonl",
    mime="application/json",
)
