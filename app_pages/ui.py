"""
ui.py — Shared look and feel for every page.

Streamlit gives you working widgets, not a designed product. This module adds the
layer between the two: page chrome, a small set of tokens, and a few composite
components used across the recruiter chat, the setup form and the admin view.

Two rules kept throughout:

  1. **Tokens, not literals.** Colours live in CSS custom properties defined once
     in `_CSS` and mirrored from .streamlit/config.toml, so the theme can change
     in one place. Streamlit's own `[theme]` block cannot express spacing, radii
     or elevation, which is why any of this is here at all.

  2. **Style, don't restructure.** Rules target documented `data-testid` hooks and
     stable class names, and every one degrades to plain Streamlit if a selector
     stops matching after an upgrade. Nothing here is load-bearing for behaviour —
     a missed selector costs polish, never function.
"""

from __future__ import annotations

import streamlit as st

# One place for the palette. Mirrors .streamlit/config.toml so widgets Streamlit
# themes natively and elements we style here cannot drift apart.
_CSS = """
<style>
:root {
  --ink:        #1B1D28;
  --ink-soft:   #5A5F73;
  --ink-faint:  #8B90A3;
  --line:       #E4E6EF;
  --surface:    #FFFFFF;
  --canvas:     #FBFBFD;
  --brand:      #4F46E5;
  --brand-soft: #EEF0FE;
  --ok:         #0F8A5F;
  --warn:       #B45309;
  --radius:     14px;
  --shadow-sm:  0 1px 2px rgba(20, 22, 40, .05);
  --shadow-md:  0 4px 16px rgba(20, 22, 40, .07);
}

/* Roomier, centred column. Streamlit's default is cramped at wide viewports and
   the measure gets uncomfortably long for reading answers. */
.block-container { max-width: 860px; padding-top: 2.4rem; padding-bottom: 6rem; }

h1, h2, h3 { letter-spacing: -0.02em; color: var(--ink); }
h1 { font-weight: 700; }
hr, [data-testid="stDivider"] { border-color: var(--line) !important; }

/* Hide the Deploy button and the hamburger menu — they point at tooling that
   isn't the recruiter's. But NOT the whole toolbar: it also contains the
   "Running…" status widget, and hiding that made long jobs (document ingestion
   runs OCR plus an LLM summary per file) look like the page had frozen, since
   Streamlit dims the view while a script runs and nothing explained why. */
[data-testid="stAppDeployButton"],
[data-testid="stMainMenu"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stStatusWidget"] { visibility: visible !important; }
footer { visibility: hidden; }

/* ── Page header ──────────────────────────────────────────────────────────── */
.app-header { display: flex; align-items: center; gap: 1rem; margin-bottom: .35rem; }
.app-avatar {
  width: 52px; height: 52px; border-radius: 50%; flex: 0 0 52px;
  display: grid; place-items: center;
  background: linear-gradient(135deg, var(--brand), #7C74F0);
  color: #fff; font-weight: 700; font-size: 1.1rem; letter-spacing: .02em;
  box-shadow: var(--shadow-md);
}
.app-title  { font-size: 1.6rem; font-weight: 700; line-height: 1.2; color: var(--ink); }
.app-sub    { font-size: .95rem; color: var(--ink-soft); margin-top: .15rem; }

.app-badge {
  display: inline-flex; align-items: center; gap: .4rem;
  background: var(--brand-soft); color: var(--brand);
  font-size: .75rem; font-weight: 600; padding: .2rem .6rem;
  border-radius: 999px; vertical-align: middle;
}

/* ── Cards ────────────────────────────────────────────────────────────────── */
.card {
  background: var(--surface); border: 1px solid var(--line);
  border-radius: var(--radius); padding: 1.15rem 1.3rem;
  box-shadow: var(--shadow-sm); margin-bottom: .9rem;
}
.card-title { font-weight: 650; color: var(--ink); margin-bottom: .3rem; }
.card-body  { color: var(--ink-soft); font-size: .92rem; line-height: 1.55; }

/* ── Chat ─────────────────────────────────────────────────────────────────── */
/* Speaker is matched on the aria-label Streamlit puts on the content wrapper.
   The role is otherwise only encoded in emotion hash classes
   (st-emotion-cache-1iitq1e), which change between releases — the aria-label is
   both stable and semantically the right thing to key on. */
[data-testid="stChatMessage"] {
  background: transparent; border: 0;
  padding: .1rem 0 .1rem; margin-bottom: .5rem;
}
/* The question: quiet, small, clearly secondary to the answer. */
[data-testid="stChatMessage"]:has([aria-label="Chat message from user"]) {
  margin-top: 1.1rem;
}
[data-testid="stChatMessage"]:has([aria-label="Chat message from user"]) p {
  color: var(--ink-soft); font-weight: 550; font-size: .93rem;
}
/* The answer: a real surface. This is the content the recruiter came for, and
   giving it a card is what separates a conversation from a wall of text. */
[data-testid="stChatMessage"]:has([aria-label="Chat message from assistant"]) {
  background: var(--surface); border: 1px solid var(--line);
  border-radius: var(--radius); padding: .95rem 1.15rem;
  box-shadow: var(--shadow-sm);
}
[data-testid="stChatMessage"] p  { line-height: 1.62; }
[data-testid="stChatMessage"] li { line-height: 1.55; }
[data-testid="stChatMessage"] p:last-child { margin-bottom: 0; }

[data-testid="stChatInput"] textarea { font-size: .97rem; }
[data-testid="stChatInput"] { border-radius: 14px; }

/* ── Suggested questions ──────────────────────────────────────────────────── */
/* Streamlit has no chip widget, so these are real buttons restyled. Keeping them
   buttons means keyboard focus and screen-reader semantics come for free.
   Scoped via st.container(key="suggestions") -> .st-key-suggestions. A wrapping
   st.markdown("<div>") does NOT work: Streamlit closes the div in its own
   element, so the widgets end up as siblings, not children. */
.st-key-suggestions [data-testid="stButton"] button {
  width: 100%; height: auto; min-height: 0;
  background: var(--surface); border: 1px solid var(--line);
  border-radius: 12px; padding: .75rem .95rem;
  box-shadow: var(--shadow-sm);
  transition: border-color .15s, box-shadow .15s, transform .15s;
  /* The button is a flex row that centres its child. Setting text-align alone
     does nothing: the label block stays centred as a flex item and only its
     internal lines align left. Both the justification and the child width have
     to change for the label to start at the padding edge. */
  justify-content: flex-start; text-align: left;
}
/* Streamlit nests button > div > span > stMarkdownContainer > p, and BOTH the
   div and the span are flex boxes that centre their child. Every level has to be
   re-justified or the label stays optically centred no matter what the button or
   the paragraph say. */
.st-key-suggestions [data-testid="stButton"] button > div,
.st-key-suggestions [data-testid="stButton"] button > div > span {
  width: 100%; justify-content: flex-start; text-align: left;
}
.st-key-suggestions [data-testid="stButton"] button [data-testid="stMarkdownContainer"] {
  width: 100%; text-align: left;
}
.st-key-suggestions [data-testid="stButton"] button p {
  text-align: left; white-space: normal; font-weight: 500;
  font-size: .88rem; line-height: 1.45; color: var(--ink); margin: 0;
}
.st-key-suggestions [data-testid="stButton"] button:hover {
  border-color: var(--brand); box-shadow: var(--shadow-md); transform: translateY(-1px);
}
.st-key-suggestions [data-testid="stButton"] button:hover p { color: var(--brand); }

/* ── Trust row (empty state) ──────────────────────────────────────────────── */
/* Fills what would otherwise be dead space between the openers and the input,
   and answers the question a recruiter actually has on arrival: can I believe
   what this thing tells me? */
.trust { display: flex; gap: .8rem; margin-top: 1.6rem; flex-wrap: wrap; }
.trust-item {
  flex: 1 1 180px; background: var(--surface); border: 1px solid var(--line);
  border-radius: 12px; padding: .8rem .9rem;
}
.trust-item .t-h {
  font-size: .82rem; font-weight: 650; color: var(--ink);
  display: flex; align-items: center; gap: .4rem; margin-bottom: .25rem;
}
.trust-item .t-b { font-size: .78rem; color: var(--ink-soft); line-height: 1.5; }

/* ── Auth gate ────────────────────────────────────────────────────────────── */
/* Kept deliberately short: the mark, one line of explanation and the field must
   all sit above the fold on a laptop, or the first thing the recruiter does is
   hunt for an input they cannot see. */
.gate { max-width: 420px; margin: .5rem auto 0; text-align: center; }
.gate-mark {
  width: 54px; height: 54px; border-radius: 16px; margin: 0 auto .9rem;
  display: grid; place-items: center; font-size: 1.4rem;
  background: linear-gradient(135deg, var(--brand), #7C74F0);
  box-shadow: var(--shadow-md);
}
.gate h2 { font-size: 1.3rem; margin: 0 0 .35rem; }
.gate p  { color: var(--ink-soft); font-size: .9rem; margin: 0 0 .4rem; }
/* The caption under the field is reassurance, not instruction — keep it quiet. */
.gate-note [data-testid="stCaptionContainer"] p {
  font-size: .78rem; color: var(--ink-faint); text-align: center;
}

/* ── Setup form sections ──────────────────────────────────────────────────── */
.sec { display: flex; align-items: center; gap: .6rem; margin: 2rem 0 .2rem; }
.sec-n {
  width: 26px; height: 26px; border-radius: 8px; flex: 0 0 26px;
  display: grid; place-items: center;
  background: var(--brand-soft); color: var(--brand);
  font-size: .8rem; font-weight: 700;
}
.sec-t { font-size: 1.12rem; font-weight: 650; color: var(--ink); }
.sec-h { color: var(--ink-soft); font-size: .87rem; margin: 0 0 .7rem 2.1rem; }

/* ── Metrics ──────────────────────────────────────────────────────────────── */
[data-testid="stMetric"] {
  background: var(--surface); border: 1px solid var(--line);
  border-radius: var(--radius); padding: .85rem 1rem; box-shadow: var(--shadow-sm);
}
[data-testid="stMetricLabel"] {
  color: var(--ink-faint) !important; font-size: .74rem !important;
  text-transform: uppercase; letter-spacing: .05em; font-weight: 600;
}
[data-testid="stMetricValue"] { font-size: 1.5rem !important; font-weight: 680; }

/* ── Forms ────────────────────────────────────────────────────────────────── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
  border-radius: 10px !important; border-color: var(--line) !important;
}
[data-testid="stFileUploaderDropzone"] {
  border-radius: var(--radius); border: 1.5px dashed var(--line);
  background: var(--surface);
}
[data-testid="stButton"] button[kind="primary"] {
  border-radius: 10px; font-weight: 600; box-shadow: var(--shadow-sm);
}

/* Narrow screens: recruiters open links on phones more often than not. */
@media (max-width: 640px) {
  .block-container { padding-top: 1.4rem; padding-left: 1rem; padding-right: 1rem; }
  .app-avatar { width: 42px; height: 42px; flex-basis: 42px; font-size: .95rem; }
  .app-title  { font-size: 1.3rem; }
}
</style>
"""


def page_setup(title: str, icon: str = "💼", *, wide: bool = False,
               sidebar: str = "auto") -> None:
    """Set the browser tab identity and inject the shared stylesheet.

    Must be the first Streamlit call on a run — st.set_page_config raises if
    anything has already rendered. Without it the tab reads "Streamlit" with the
    stock icon, which is the first thing a recruiter sees when they open the link.
    """
    try:
        st.set_page_config(
            page_title=title,
            page_icon=icon,
            layout="wide" if wide else "centered",
            initial_sidebar_state=sidebar,
        )
    except Exception:
        # Already configured earlier in this run (multi-page navigation re-executes
        # the entry script). Styling below still needs to apply.
        pass
    st.markdown(_CSS, unsafe_allow_html=True)


def inject_css() -> None:
    """Re-apply the stylesheet on a page that didn't call page_setup()."""
    st.markdown(_CSS, unsafe_allow_html=True)


def initials(name: str) -> str:
    """Two-letter monogram for the avatar. Falls back to a neutral mark so the
    header still looks deliberate before a profile exists."""
    parts = [p for p in (name or "").replace("-", " ").split() if p[:1].isalpha()]
    if not parts:
        return "AI"
    return (parts[0][0] + (parts[-1][0] if len(parts) > 1 else "")).upper()


def header(title: str, subtitle: str = "", *, monogram: str = "AI",
           badge: str | None = None) -> None:
    """Avatar + title + subtitle block used at the top of each page."""
    badge_html = f'<span class="app-badge">{badge}</span>' if badge else ""
    st.markdown(
        f"""
        <div class="app-header">
          <div class="app-avatar">{monogram}</div>
          <div>
            <div class="app-title">{title} {badge_html}</div>
            <div class="app-sub">{subtitle}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section(step: int, title: str, hint: str = "") -> None:
    """Numbered section heading for the setup form.

    The form is long enough that a flat run of equal-weight headers reads as an
    endless scroll; numbering it turns the same content into visible progress.
    """
    st.markdown(
        f"""
        <div class="sec">
          <span class="sec-n">{step}</span>
          <span class="sec-t">{title}</span>
        </div>
        {f'<div class="sec-h">{hint}</div>' if hint else ""}
        """,
        unsafe_allow_html=True,
    )


def card(title: str, body: str) -> None:
    st.markdown(
        f'<div class="card"><div class="card-title">{title}</div>'
        f'<div class="card-body">{body}</div></div>',
        unsafe_allow_html=True,
    )
