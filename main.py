import streamlit as st

import settings as config  # module named `settings` to avoid shadowing the scorer's `config`
from auth import require_auth

# Gate the whole app behind the shared access code (no-op if APP_PASSWORD unset).
require_auth()

# In production, serve ONLY the recruiter chat — the Candidate Setup page (which
# can edit your profile and trigger ingestion) must never be reachable by a
# recruiter. Run locally with APP_MODE=setup to expose it for profile updates.
pages = [st.Page("pages/recruiter.py", title="Recruiter Chat")]
if config.APP_MODE != "production":
    pages.insert(0, st.Page("pages/setup.py", title="Candidate Setup"))

pg = st.navigation(pages)
pg.run()
