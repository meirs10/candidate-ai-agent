import uuid

import streamlit as st

from agent.agent import run
from auth import require_auth
from store.structured import load as load_profile
from app_pages import ui

require_auth()  # defense in depth; main.py gates too (no-op once authenticated)
ui.inject_css()

# The header is personalised from the saved profile, so the recruiter lands on
# "Ask about Dana Levy", not a generic product name. Every field is optional —
# before a profile exists the page still has to look finished, so each one falls
# back rather than rendering an empty slot.
_profile = load_profile()
_name = (_profile.get("full_name") or "").strip()
_role = (_profile.get("current_role") or _profile.get("desired_job_title") or "").strip()

ui.header(
    f"Ask about {_name}" if _name else "Ask about the candidate",
    _role or "Background, skills, experience and availability",
    monogram=ui.initials(_name),
    badge="AI assistant",
)
st.write("")

if "history" not in st.session_state:
    st.session_state.history = []

# Stable per-browser-session id so the telemetry log can be read back as threads
# rather than a flat list of unrelated questions. Random and opaque: it is not
# tied to any identity, it only groups one visit's turns together.
if "session_id" not in st.session_state:
    st.session_state.session_id = uuid.uuid4().hex[:10]

AVATARS = {"user": "🧑‍💼", "assistant": "💬"}

# Openers for the empty state. Chosen to cover the four tools — a fixed field, a
# skill, a document search and a question about the system itself — so the first
# click demonstrates the range instead of just answering one thing.
SUGGESTIONS = [
    "What's their strongest technical skill, and what's the evidence?",
    "Walk me through their most significant project.",
    "What's their availability and preferred work setup?",
    "How does this AI assistant actually work?",
]


def _ask(question: str) -> None:
    """Run one turn and append it to the visible history."""
    with st.chat_message("user", avatar=AVATARS["user"]):
        st.write(question)
    try:
        with st.chat_message("assistant", avatar=AVATARS["assistant"]):
            with st.spinner("Searching the candidate's documents…"):
                answer, updated_history, _ = run(
                    st.session_state.history.copy(), question,
                    session_id=st.session_state.session_id,
                )
            st.write(answer)
    except Exception as exc:  # a friendly message beats a stack trace
        st.chat_message("assistant", avatar=AVATARS["assistant"]).error(
            "Sorry — I couldn't answer that just now. Please try again in a moment."
        )
        st.caption(f"(details: {type(exc).__name__})")
    else:
        st.session_state.history = updated_history


# ── Conversation ─────────────────────────────────────────────────────────────
for msg in st.session_state.history:
    role = msg["role"]
    st.chat_message(role, avatar=AVATARS.get(role)).write(msg["content"])

# ── Empty state ──────────────────────────────────────────────────────────────
# A bare chat box gives a recruiter no idea what this thing knows. Offering four
# concrete openers is the difference between a demo they try and one they bounce
# off; it also sets the expectation that questions can be substantive.
pending = st.session_state.pop("_pending_question", None)

if not st.session_state.history and not pending:
    st.markdown("###### Try asking")
    # key= gives the container a `.st-key-suggestions` class, which is the only
    # reliable way to scope CSS to these widgets — a wrapping markdown <div>
    # leaves them as siblings rather than children.
    with st.container(key="suggestions"):
        left, right = st.columns(2)
        for i, suggestion in enumerate(SUGGESTIONS):
            with (left, right)[i % 2]:
                if st.button(suggestion, key=f"suggest_{i}", use_container_width=True):
                    # Set and rerun rather than answering inline, so the grid
                    # disappears in the same frame the answer starts rendering.
                    st.session_state["_pending_question"] = suggestion
                    st.rerun()

    st.markdown(
        """
        <div class="trust">
          <div class="trust-item">
            <div class="t-h">📄 Grounded in real documents</div>
            <div class="t-b">Every answer is drawn from the candidate's CV,
            certificates and project write-ups — not from a model's memory.</div>
          </div>
          <div class="trust-item">
            <div class="t-h">🤐 Admits the gaps</div>
            <div class="t-b">If the documents don't cover something, it says so
            instead of filling the space with a plausible guess.</div>
          </div>
          <div class="trust-item">
            <div class="t-h">💼 Professional scope</div>
            <div class="t-b">It answers career questions only, and declines
            personal ones.</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ── Input ────────────────────────────────────────────────────────────────────
typed = st.chat_input("Ask about experience, skills, projects, availability…")
question = pending or typed
if question:
    _ask(question)
    if pending:
        # The suggestion grid was skipped this run; redraw so the history renders
        # through the normal path and the input clears.
        st.rerun()
