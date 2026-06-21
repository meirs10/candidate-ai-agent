"""
E2E smoke test for the agent pipeline.

Mocks heavy external dependencies (Ollama, ChromaDB, embedding/reranker models)
at the module level so the test runs without external services, but exercises
the full agent wiring: run() -> tool dispatch -> structured store -> answer assembly.
"""

import json
import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Pre-mock heavy external dependencies BEFORE importing any project code.
# This prevents chromadb, ollama, sentence-transformers, torch, etc. from
# being loaded -- they aren't needed since we mock the agent's LLM calls.
# ---------------------------------------------------------------------------

# ollama (used by agent.llm and rag.retriever)
sys.modules.setdefault("ollama", MagicMock())

# rag.retriever and its transitive deps (chromadb, embedder, reranker, bm25)
# We replace the entire module so agent.tools gets a mock `retrieve` function.
if "rag.retriever" not in sys.modules:
    _mock_retriever_mod = ModuleType("rag.retriever")
    _mock_retriever_mod.retrieve = MagicMock(
        return_value={
            "chunks": [],
            "route": "SPECIFIC",
            "expanded_queries": [],
            "fused_pool": [],
        }
    )
    sys.modules["rag.retriever"] = _mock_retriever_mod

for _mod in ("chromadb", "rank_bm25", "rag.embedder", "rag.reranker"):
    sys.modules.setdefault(_mod, MagicMock())

# Now it's safe to import project code ----------------------------------------
from agent.agent import run  # isort: skip


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def _candidate_store(tmp_path, monkeypatch):
    """Write a minimal candidate.json and point the structured store at it."""
    candidate_data = {
        "full_name": "Ada Lovelace",
        "email_address": "ada@example.com",
        "years_of_experience": "5",
        "current_role": "Senior Engineer",
        "desired_job_title": "Staff Engineer",
        "education": [
            {
                "degree_title": "BSc",
                "field_of_study": "Computer Science",
                "institution": "University of London",
                "graduation_year": "2019",
                "gpa": "3.9",
            }
        ],
        "skills": ["Python", "AWS"],
        "skill_scores": [
            {"skill": "Python", "level": 4, "chunks": ["Built REST APIs..."]},
            {"skill": "AWS", "level": 3, "chunks": ["Deployed services on EC2..."]},
        ],
    }
    data_dir = tmp_path / "store" / "data"
    data_dir.mkdir(parents=True)
    data_file = data_dir / "candidate.json"
    data_file.write_text(json.dumps(candidate_data))

    # Point the structured store module at our temp file
    monkeypatch.setattr("store.structured.DATA_PATH", str(data_file))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_tool_call_responses(tool_name, tool_args, final_answer):
    """Return a side_effect callable simulating Ollama's tool-calling protocol.

    Call 1: LLM decides to call `tool_name` with `tool_args`
    Call 2: LLM produces `final_answer` using the tool result
    """
    responses = iter(
        [
            {
                "message": {
                    "content": "",
                    "tool_calls": [
                        {"function": {"name": tool_name, "arguments": tool_args}}
                    ],
                }
            },
            {"message": {"content": final_answer}},
        ]
    )
    return lambda **kwargs: next(responses)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.e2e
@pytest.mark.usefixtures("_candidate_store")
class TestAgentSmoke:
    """Smoke tests for the agent pipeline with mocked externals."""

    def test_run_returns_answer_with_tool_call(self):
        """agent.run() dispatches a tool, feeds the result back, and returns
        a non-empty answer containing expected content."""

        mock_call = _make_tool_call_responses(
            tool_name="get_structured_data",
            tool_args={"field": "full_name"},
            final_answer="The candidate's name is Ada Lovelace.",
        )

        with patch("agent.agent.llm.call", side_effect=mock_call):
            answer, history, trajectory = run([], "What is the candidate's name?")

        # Answer is non-empty and contains the name from our fixture
        assert answer, "Agent returned an empty answer"
        assert "Ada Lovelace" in answer

        # Conversation history was updated (user + assistant)
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"

        # Tool trajectory recorded the structured-data lookup
        assert len(trajectory) == 1
        assert trajectory[0]["tool"] == "get_structured_data"
        assert "Ada Lovelace" in trajectory[0]["result_preview"]

    def test_run_no_tool_call(self):
        """When the LLM answers directly (no tool call), agent.run() still
        returns a valid response."""

        direct_response = {
            "message": {
                "content": "Hello! I'm the candidate's AI representative.",
            }
        }

        with patch("agent.agent.llm.call", return_value=direct_response):
            answer, history, trajectory = run([], "Hi there!")

        assert answer, "Agent returned an empty answer"
        assert "representative" in answer.lower() or "hello" in answer.lower()
        assert len(history) == 2
        assert trajectory == []

    def test_run_skill_proficiency_tool(self):
        """agent.run() can dispatch get_skill_proficiency and return a
        level-based answer."""

        mock_call = _make_tool_call_responses(
            tool_name="get_skill_proficiency",
            tool_args={"skill": "Python"},
            final_answer="The candidate has a strong proficiency (level 4/5) in Python.",
        )

        with patch("agent.agent.llm.call", side_effect=mock_call):
            answer, _history, trajectory = run([], "How good is the candidate at Python?")

        assert answer, "Agent returned an empty answer"
        assert "4" in answer or "strong" in answer.lower()
        assert trajectory[0]["tool"] == "get_skill_proficiency"
