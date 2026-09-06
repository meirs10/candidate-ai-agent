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

import streamlit as st
import streamlit.components.v1 as components

import settings as config  # module named `settings` to avoid shadowing the scorer's `config`
from app_pages import ui

_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"

# The widget lives in a sandboxed component iframe and cannot touch session
# state, so the token comes back through the URL: the iframe rewrites the parent
# location with ?bot=<token>, the page reloads, and the server verifies it. One
# extra page load, once per visitor.
_TOKEN_PARAM = "bot"


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


def _challenge_html(site_key: str) -> str:
    """The Turnstile widget, plus the hand-off that returns its token.

    The callback rewrites the PARENT url because the widget renders inside
    Streamlit's component iframe; setting the iframe's own location would just
    reload the iframe and lose the token.
    """
    return f"""
<div id="cf-turnstile-host" style="display:flex;justify-content:center;padding:4px 0;"></div>
<script src="https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit" async defer></script>
<script>
  function handOffToken(token) {{
    try {{
      var url = new URL(window.parent.location.href);
      url.searchParams.set({_TOKEN_PARAM!r}, token);
      window.parent.location.replace(url.toString());
    }} catch (e) {{
      // Cross-origin parent (shouldn't happen for a first-party component, but
      // fail visibly rather than hanging on a spinner forever).
      document.getElementById('cf-turnstile-host').innerHTML =
        '<p style="font:14px system-ui;color:#b91c1c">Could not complete the check. Please reload the page.</p>';
    }}
  }}
  function renderWidget() {{
    if (!window.turnstile) {{ return setTimeout(renderWidget, 120); }}
    window.turnstile.render('#cf-turnstile-host', {{
      sitekey: {site_key!r},
      callback: handOffToken,
      'error-callback': function () {{ handOffToken(''); }},
      theme: 'light',
    }});
  }}
  renderWidget();
</script>
"""


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

    # Returning from the widget: verify, then strip the token from the URL so it
    # is not sitting in the address bar or a shared link. Tokens are single-use,
    # so a copied URL would fail anyway and look like a broken link.
    token = str(st.query_params.get(_TOKEN_PARAM, "") or "")
    if token:
        ok = _verify_token(token)
        try:
            del st.query_params[_TOKEN_PARAM]
        except Exception:
            pass
        if ok:
            st.session_state["_bot_ok"] = True
            st.rerun()

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
        components.html(_challenge_html(config.TURNSTILE_SITE_KEY), height=90)
        if token:
            # We got here with a token that did not verify.
            st.error("That check didn't go through. Please try again.")
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
