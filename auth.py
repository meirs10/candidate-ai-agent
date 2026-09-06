"""
auth.py — Minimal shared-secret gate for the recruiter chat.

Single-candidate app: there's exactly one person to protect and one link to
hand out, so a single access code (set via the APP_PASSWORD secret) is the right
strength. With no APP_PASSWORD configured the gate is a no-op — convenient for
local development.
"""

import hmac

import streamlit as st

import settings as config  # module named `settings` to avoid shadowing the scorer's `config`
from app_pages import ui


def require_auth() -> None:
    """Block rendering until the correct access code is entered.

    No-op when APP_PASSWORD is unset. Once authenticated, the result is cached in
    session state so the recruiter isn't re-prompted on every interaction.

    This screen is the first thing a recruiter sees, so it is treated as part of
    the product rather than a debug prompt: centred card, a plain explanation of
    what they've reached, and an error only once they've actually typed something
    wrong.
    """
    password = config.APP_PASSWORD
    if not password:
        return
    if st.session_state.get("_authed"):
        return

    ui.inject_css()
    st.markdown(
        """
        <div class="gate">
          <div class="gate-mark">🔐</div>
          <h2>Private candidate profile</h2>
          <p>Enter the access code included in the link you were sent.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _, mid, _ = st.columns([1, 2.2, 1])
    with mid:
        entered = st.text_input(
            "Access code", type="password", label_visibility="collapsed",
            placeholder="Access code",
        )
        if entered:
            # compare_digest: a plain == leaks the secret's length and matching
            # prefix through timing, and this endpoint is public.
            if hmac.compare_digest(entered, password):
                st.session_state["_authed"] = True
                st.rerun()
            else:
                st.error("That code doesn't match. Check the link you were sent.")
        st.markdown('<div class="gate-note">', unsafe_allow_html=True)
        st.caption("Shared privately. If your code has expired, ask for a new link.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()
