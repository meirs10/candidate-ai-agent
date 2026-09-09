import uuid

import streamlit as st

import ratelimit
from agent.agent import run_streaming
from app_pages import ui
from app_pages.text_direction import is_rtl
from auth import require_auth, require_bot_check
from store.structured import load as load_profile

# Two gates, in cost order. The bot check is what protects the public link; the
# access code is a no-op unless APP_PASSWORD is still configured.
require_bot_check()
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


def _rtl_message_css(key: str) -> None:
    """Force right-to-left rendering for one chat message container.

    `unicode-bidi: plaintext` alone (see ui.py's chat-message CSS) reorders
    characters within a line correctly per the Unicode Bidi Algorithm, but
    does not reliably flip which side text-align:start resolves to — a
    Hebrew paragraph inside the page's LTR root can end up bidi-reordered yet
    still block-aligned to the left, which is exactly the "right words, wrong
    side" look a recruiter reported. Setting `direction: rtl` explicitly,
    scoped to just this message's container key, is unambiguous: no content
    detection at render time, no cross-browser guessing.

    Scoped per message (not the whole page) because a conversation mixes
    languages turn by turn, and an English answer must stay left-aligned.
    """
    st.markdown(
        f'<style>.st-key-{key} p, .st-key-{key} li '
        f'{{ direction: rtl; text-align: right; unicode-bidi: plaintext; }}</style>',
        unsafe_allow_html=True,
    )


def _render_message(role: str, content: str, key: str) -> None:
    """Render one chat message, applying RTL styling when its text needs it.

    Wrapped in st.container(key=...) because that is the only way to reach a
    specific message with CSS — Streamlit gives each container a stable
    `.st-key-<key>` class, but chat_message() itself takes no such hook in
    this Streamlit version.
    """
    with st.chat_message(role, avatar=AVATARS.get(role)):
        with st.container(key=key):
            st.write(content)
        if is_rtl(content):
            _rtl_message_css(key)


# Openers for the empty state. Chosen to cover the four tools — a fixed field, a
# skill, a document search and a question about the system itself — so the first
# click demonstrates the range instead of just answering one thing.
SUGGESTIONS = [
    "What's his strongest technical skill, and what's the evidence?",
    "Walk me through his most significant project.",
    "What's his availability and preferred work setup?",
    "How does this AI assistant actually work?",
]


def _ask(question: str) -> None:
    """Run one turn and append it to the visible history."""
    # Keys mirror the index this turn's messages will occupy once appended to
    # history, so the SAME key styles the message during the live typing
    # effect and again on the next rerun, when the top-of-page loop redraws
    # it from st.session_state.history.
    user_key = f"msg-{len(st.session_state.history)}"
    assistant_key = f"msg-{len(st.session_state.history) + 1}"

    with st.chat_message("user", avatar=AVATARS["user"]):
        with st.container(key=user_key):
            st.write(question)
        if is_rtl(question):
            _rtl_message_css(user_key)

    # Checked here rather than at the top of the page: a rerun costs nothing,
    # but a question costs a routing call, up to four tools, embeddings, a
    # rerank and a synthesis call. The limit belongs on the expensive action.
    allowed, retry_after = ratelimit.check()
    if not allowed:
        with st.chat_message("assistant", avatar=AVATARS["assistant"]):
            st.warning(
                f"That's a lot of questions at once — give me about "
                f"{retry_after} seconds and ask again."
            )
        return

    try:
        with st.chat_message("assistant", avatar=AVATARS["assistant"]):
            # The answer's own direction isn't known until it's fully
            # generated, but the synthesis prompt guarantees it matches the
            # recruiter's language — so the question's direction is applied
            # up front, before the first token arrives, rather than snapping
            # the alignment into place after the fact.
            if is_rtl(question):
                _rtl_message_css(assistant_key)
            with st.container(key=assistant_key):
                turn = run_streaming(
                    st.session_state.history.copy(), question,
                    session_id=st.session_state.session_id,
                )
                # The spinner covers routing and tool execution — the silent
                # part. It is closed by the first streamed fragment, so the
                # recruiter sees "searching", then words appearing, with no
                # dead gap between them.
                with st.spinner("Searching the candidate's documents…"):
                    stream = iter(turn)
                    first = next(stream, "")

                def _rest():
                    if first:
                        yield first
                    yield from stream

                st.write_stream(_rest())
    except Exception as exc:  # a friendly message beats a stack trace
        st.chat_message("assistant", avatar=AVATARS["assistant"]).error(
            "Sorry — I couldn't answer that just now. Please try again in a moment."
        )
        st.caption(f"(details: {type(exc).__name__})")
    else:
        st.session_state.history = turn.history


# ── Conversation ─────────────────────────────────────────────────────────────
for _i, msg in enumerate(st.session_state.history):
    _render_message(msg["role"], msg["content"], key=f"msg-{_i}")

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
