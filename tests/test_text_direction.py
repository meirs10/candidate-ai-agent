"""
Tests for app_pages.text_direction — the RTL detection behind the recruiter
chat's per-message direction fix.

A Hebrew answer used to render bidi-reordered but still block-aligned to the
left, because unicode-bidi: plaintext alone does not reliably flip which side
text-align:start resolves to. The fix scopes an explicit direction: rtl to
just the messages that need it, decided by this module.
"""

import pytest

from app_pages.text_direction import is_rtl


class TestIsRtl:

    @pytest.mark.parametrize("text", [
        "מה החוזקות שלו?",
        "הוא יודע להשתמש ב-Docker",          # mixed Hebrew + Latin technical term
        "מרحبا",                              # Hebrew + Arabic mixed
        "שלום",
    ])
    def test_detects_hebrew_and_arabic(self, text):
        assert is_rtl(text) is True

    @pytest.mark.parametrize("text", [
        "What's his strongest technical skill?",
        "Docker, PyTorch, RunPod",
        "12345 - !@#$%^&*()",
        "",
    ])
    def test_leaves_latin_and_neutral_text_alone(self, text):
        assert is_rtl(text) is False

    def test_a_single_rtl_word_is_enough(self):
        """"Contains any", not "is majority" — the synthesis prompt guarantees
        a single-language answer, so one RTL word already means the whole
        message is RTL; no need to count characters."""
        assert is_rtl("Built with PyTorch and RunPod עבור לקוח") is True

    def test_none_is_not_rtl(self):
        assert is_rtl(None) is False
