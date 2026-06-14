"""
auth.py — Minimal shared-secret gate for the recruiter chat.

Single-candidate app: there's exactly one person to protect and one link to
hand out, so a single access code (set via the APP_PASSWORD secret) is the right
strength. With no APP_PASSWORD configured the gate is a no-op — convenient for
local development.
"""

import streamlit as st

import config


def require_auth() -> None:
    """Block rendering until the correct access code is entered.

    No-op when APP_PASSWORD is unset. Once authenticated, the result is cached in
    session state so the recruiter isn't re-prompted on every interaction.
    """
    password = config.APP_PASSWORD
    if not password:
        return
    if st.session_state.get("_authed"):
        return

    st.title("🔒 Protected")
    st.caption("Enter the access code from the link you were sent.")
    entered = st.text_input("Access code", type="password")
    if entered:
        if entered == password:
            st.session_state["_authed"] = True
            st.rerun()
        else:
            st.error("Incorrect access code.")
    st.stop()
