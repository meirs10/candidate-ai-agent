"""
text_direction.py — Detect right-to-left text.

Kept dependency-free and separate from the recruiter page (which is a
Streamlit script, not an importable module — it runs page-level code such as
require_bot_check() at import time) so this one function can be unit tested
directly, the same reason rag/ingest_types.py was split out of rag/ingest.py.
"""

from __future__ import annotations

import re

# Hebrew (\u0590-\u05FF) and Arabic, including its Presentation Forms and the
# Extended-A block used by Persian/Urdu (\u0600-\u06FF, \u0750-\u077F,
# \uFB50-\uFDFF, \uFE70-\uFEFF). "Contains any", not "is majority": the
# synthesis prompt guarantees the agent answers in the recruiter's own
# language, so a single RTL word already means the whole message is RTL.
_RTL_RE = re.compile(
    "[\u0590-\u05FF\u0600-\u06FF\u0750-\u077F\uFB1D-\uFDFF\uFE70-\uFEFF]"
)


def is_rtl(text: str) -> bool:
    """True if `text` contains any Hebrew or Arabic-script character."""
    return bool(_RTL_RE.search(text or ""))
