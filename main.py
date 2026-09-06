import hmac

import streamlit as st

import settings as config  # module named `settings` to avoid shadowing the scorer's `config`
from app_pages import ui
from auth import require_auth

# Must run before anything renders. Also the only place the browser tab gets a
# name — without it recruiters see "Streamlit" and the stock icon in their tab
# bar, which is the first impression the link makes.
ui.page_setup("Candidate AI Agent", icon="💼")


def _is_admin() -> bool:
    """True when this session arrived with ?admin=<ADMIN_PASSWORD>.

    Deliberately a query parameter rather than a sidebar entry: a recruiter with
    the chat link must not be able to see that a usage dashboard exists, let
    alone that it holds every conversation. Unset ADMIN_PASSWORD → no dashboard
    at all, so a deployment that never configures one cannot expose it.

    The result is latched into session state because Streamlit's own navigation
    links do not carry the query string — without the latch, clicking through to
    the dashboard drops `?admin=`, which de-registers the page mid-navigation and
    bounces you back to the chat.

    compare_digest, not ==, so the check does not leak the secret's length or
    prefix through response timing.
    """
    if not config.ADMIN_PASSWORD:
        return False
    if st.session_state.get("_is_admin"):
        return True
    supplied = str(st.query_params.get("admin", ""))
    if supplied and hmac.compare_digest(supplied, config.ADMIN_PASSWORD):
        st.session_state["_is_admin"] = True
        return True
    return False


# Gate the whole app behind the shared access code (no-op if APP_PASSWORD unset).
require_auth()

# In production, serve ONLY the recruiter chat — the Candidate Setup page (which
# can edit your profile and trigger ingestion) must never be reachable by a
# recruiter. Run locally with APP_MODE=setup to expose it for profile updates.
# NOTE: this directory must NOT be called "pages/". Streamlit auto-discovers a
# directory with that exact name and publishes every file in it as its own route,
# in ADDITION to the st.navigation() menu built here — and those auto-routes skip
# main.py entirely, so they bypass both require_auth() and the APP_MODE check
# below. Hitting /setup directly then exposes the profile editor to anyone.
pages = [st.Page("app_pages/recruiter.py", title="Recruiter Chat")]
if config.APP_MODE != "production":
    pages.insert(0, st.Page("app_pages/setup.py", title="Candidate Setup"))
if _is_admin():
    pages.append(st.Page("app_pages/admin.py", title="Usage & Conversations"))

pg = st.navigation(pages)
pg.run()
