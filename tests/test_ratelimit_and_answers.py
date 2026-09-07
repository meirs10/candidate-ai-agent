"""
Tests for the public-link protections added alongside the open recruiter URL:
the flood limiter, and the answer-opener cleanup.

Neither touches an LLM or the network, so the whole file runs offline.
"""

import pytest

import ratelimit
import settings as config
from agent.agent import _stream_without_preamble, strip_preamble


@pytest.fixture(autouse=True)
def _clean_limiter():
    ratelimit.reset()
    yield
    ratelimit.reset()


# ── Rate limiting ────────────────────────────────────────────────────────────

class TestRateLimit:

    def test_allows_up_to_the_minute_limit(self):
        limit = config.RATE_LIMIT_PER_MINUTE
        allowed = [ratelimit.check("client-a")[0] for _ in range(limit)]
        assert all(allowed), "a client was blocked before reaching the limit"

    def test_blocks_past_the_limit(self):
        for _ in range(config.RATE_LIMIT_PER_MINUTE):
            ratelimit.check("client-a")
        ok, retry_after = ratelimit.check("client-a")
        assert ok is False
        assert retry_after > 0, "a blocked caller must be told when to come back"

    def test_limit_is_per_client(self):
        for _ in range(config.RATE_LIMIT_PER_MINUTE + 5):
            ratelimit.check("noisy")
        assert ratelimit.check("quiet")[0] is True, \
            "one flooding client must not lock out everyone else"

    def test_blocked_attempts_do_not_extend_the_block(self):
        """A blocked call must not be recorded.

        Otherwise a bot that keeps hammering keeps its own window permanently
        full and is banned rather than throttled — and so is any real person
        sharing its address.
        """
        for _ in range(config.RATE_LIMIT_PER_MINUTE):
            ratelimit.check("client-a")
        first = ratelimit.check("client-a")[1]
        for _ in range(20):
            ratelimit.check("client-a")
        assert ratelimit.check("client-a")[1] <= first

    def test_generous_enough_for_a_human(self):
        """Guards the intent, not the number: a person cannot read an answer and
        ask again more than a few times a minute, so the ceiling must sit well
        above that or it will fire on genuine use."""
        assert config.RATE_LIMIT_PER_MINUTE >= 10
        assert config.RATE_LIMIT_PER_HOUR >= 60

    def test_disabled_flag_allows_everything(self, monkeypatch):
        monkeypatch.setattr(config, "RATE_LIMIT_ENABLED", False)
        assert all(ratelimit.check("client-a")[0] for _ in range(500))


# ── Answer openers ───────────────────────────────────────────────────────────

class TestStripPreamble:

    @pytest.mark.parametrize("text, expected_start", [
        ("Based on the evidence, their strongest skill is Python.", "Their"),
        ("Based on the retrieved information, they hold a B.Sc.", "They"),
        ("Based on the candidate's profile, they start immediately.", "They"),
        ("According to the documents, he built a trading bot.", "He"),
        ("The retrieved information shows that they used PyTorch.", "They"),
        ("Per the provided materials, she led the migration.", "She"),
    ])
    def test_strips_lookup_narration(self, text, expected_start):
        assert strip_preamble(text).startswith(expected_start)

    @pytest.mark.parametrize("text", [
        # "Based on" that is part of the answer, not a lookup announcement.
        "Based on their PPO work, the reward balances three objectives.",
        "The documents were written in 2026 and cover four projects.",
        "They are available immediately.",
        "Their salary expectation is listed, based on the profile.",
    ])
    def test_leaves_real_content_alone(self, text):
        assert strip_preamble(text) == text

    def test_recapitalises_past_markdown(self):
        out = strip_preamble("Based on the evidence, **diarization** is strongest.")
        assert out.startswith("**Diarization**"), out

    def test_never_empties_an_answer(self):
        """An answer that is nothing but the preamble is left intact rather than
        blanked — a stub reply beats no reply at all."""
        text = "Based on the retrieved information, yes."
        assert strip_preamble(text).strip()

    def test_stream_strips_without_buffering_everything(self):
        """The opener is cleaned mid-stream, and the tail still flows through."""
        tokens = ["Based ", "on the ", "evidence, ", "they ", "use ", "Python. "]
        tokens += [f"word{i} " for i in range(200)]
        out = "".join(_stream_without_preamble(iter(tokens)))
        assert out.startswith("They use Python.")
        assert out.rstrip().endswith("word199")

    def test_stream_handles_answer_shorter_than_the_buffer(self):
        out = "".join(_stream_without_preamble(iter(["Based on the evidence, ", "yes it is."])))
        assert out.startswith("Yes it is.")
