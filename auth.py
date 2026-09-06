"""
auth.py — Gates for the recruiter chat.

Two independent gates, and they protect against different things:

  require_bot_check()  A Cloudflare Turnstile challenge. The recruiter link is
                       public — nobody is handed a code — so the thing standing
                       between an open chat box and an unattended script is a bot
                       check, not a secret. Most visitors pass it invisibly.

  require_auth()       The legacy shared access code (APP_PASSWORD). Retained
                       because the setup page still uses it, and because leaving
                       it configured is a valid way to run a fully private link.
                       Unset → no-op.

Both are no-ops when unconfigured, which keeps local development friction-free.

Why the challenge is verified server-side: the widget hands the browser a token,
and a browser is not a trusted narrator. A bot can render the page, skip the
widget entirely and post whatever it likes. The token only means something once
Cloudflare has confirmed it, once, from here.
"""

from __future__ import annotations

import hmac
import os

import streamlit as st
import streamlit.components.v1 as components

import settings as config  # module named `settings` to avoid shadowing the scorer's `config`
from app_pages import ui

_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"

# The widget runs in a declared component rather than components.html. On
# Streamlit Cloud the component iframe is served from a different origin than
# the app, so the obvious approach — have the callback rewrite the parent URL
# with ?bot=<token> — throws a cross-origin SecurityError and the visitor sees
# "Could not complete the check". postMessage crosses that boundary legitimately,
# and a declared component is Streamlit's own postMessage channel, so the token
# comes back as a component value.
_COMPONENT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "components", "turnstile")
_turnstile_component = components.declare_component("turnstile", path=_COMPONENT_DIR)


def _verify_token(token: str) -> bool:
    """Ask Cloudflare whether this token is genuine. False on any doubt."""
    import requests

    try:
        resp = requests.post(
            _VERIFY_URL,
            data={"secret": config.TURNSTILE_SECRET_KEY, "response": token},
            timeout=10,
        )
        return bool(resp.json().get("success"))
    except Exception:
        # A network blip must not become an open door.
        return False


def require_bot_check() -> None:
    """Block rendering until the visitor clears the Turnstile challenge.

    No-op when either Turnstile key is unset. Once cleared, the result is cached
    in session state so a recruiter is challenged once per visit, not per
    question.
    """
    if not (config.TURNSTILE_SITE_KEY and config.TURNSTILE_SECRET_KEY):
        return
    if st.session_state.get("_bot_ok"):
        return

    ui.inject_css()
    st.markdown(
        """
        <div class="gate">
          <div class="gate-mark">👋</div>
          <h2>Just checking you're human</h2>
          <p>This takes a second and usually needs nothing from you.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _, mid, _ = st.columns([1, 2.2, 1])
    with mid:
        token = _turnstile_component(sitekey=config.TURNSTILE_SITE_KEY,
                                     key="turnstile", default=None)

        # A token is single-use and Cloudflare rejects a replay, so verify each
        # one exactly once. Without this guard the same token is re-verified on
        # every rerun and the second attempt fails, locking out a visitor who
        # had already passed.
        if token and token != st.session_state.get("_bot_token_seen"):
            st.session_state["_bot_token_seen"] = token
            if _verify_token(token):
                st.session_state["_bot_ok"] = True
                st.rerun()
            else:
                st.error("That check didn't go through. Please reload and try again.")

        st.markdown('<div class="gate-note">', unsafe_allow_html=True)
        st.caption("Protects the assistant from automated traffic. No cookies, no tracking.")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()


def require_auth() -> None:
    """Block rendering until the correct access code is entered.

    No-op when APP_PASSWORD is unset — which is the expected configuration for
    the public recruiter link, where require_bot_check() is the gate instead.
    Once authenticated, the result is cached in session state so the visitor
    isn't re-prompted on every interaction.

    Still used unconditionally by the setup page, which must never be open.

    This screen is treated as part of the product rather than a debug prompt:
    centred card, a plain explanation of what they've reached, and an error only
    once they've actually typed something wrong.
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
