"""
E2E smoke test for the agent pipeline.

Mocks the heavy external dependencies (LLM providers, ChromaDB, embedding and
reranker models) at module level so this runs with no services and no API keys,
while still exercising the real wiring: score_tools -> tool dispatch ->
structured store -> synthesis -> answer.

This is the test CI runs on every push, so it must stay offline and fast.

Note on shape: the agent is NOT a ReAct loop. One routing call scores every tool
0..1, each tool above the threshold runs concurrently, and a single synthesis
call answers from their combined output. So a turn mocks two things — the
router's JSON and the synthesis text — not a sequence of tool-call messages.
"""

import json
import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Pre-mock heavy external dependencies BEFORE importing any project code, so
# chromadb, torch, sentence-transformers and friends are never imported.
# ---------------------------------------------------------------------------

sys.modules.setdefault("ollama", MagicMock())

# Replace rag.retriever wholesale so agent.agent gets a mock `retrieve`.
if "rag.retriever" not in sys.modules:
    _mock_retriever_mod = ModuleType("rag.retriever")
    _mock_retriever_mod.retrieve = MagicMock(
        return_value={
            "chunks": [],
            "route": "specific",
            "expanded_queries": [],
            "fused_pool": [],
        }
    )
    sys.modules["rag.retriever"] = _mock_retriever_mod

for _mod in ("chromadb", "rank_bm25", "rag.embedder", "rag.reranker"):
    sys.modules.setdefault(_mod, MagicMock())

# Now it's safe to import project code ----------------------------------------
from agent.agent import run  # isort: skip
from agent.tool_router import TOOL_NAMES  # isort: skip


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
        "availability": "Immediately",
        "work_type": "Hybrid",
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
        # Evidence only — the scorer's 1-5 level is candidate-private and is
        # never persisted, so nothing here may carry one.
        "skill_evidence": [
            {"skill": "Python", "chunks": ["Built REST APIs..."], "doc_ids": ["cv.md"]},
            {"skill": "AWS", "chunks": ["Deployed services on EC2..."], "doc_ids": ["cv.md"]},
        ],
    }
    data_dir = tmp_path / "store" / "data"
    data_dir.mkdir(parents=True)
    data_file = data_dir / "candidate.json"
    data_file.write_text(json.dumps(candidate_data), encoding="utf-8")

    monkeypatch.setattr("store.structured.DATA_PATH", str(data_file))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _router_json(scores: dict) -> str:
    """Build the router's reply: every tool scored, with its call argument.

    Tools omitted from `scores` are scored 0.0, which is what an out-of-scope
    question looks like to the agent.
    """
    payload = {}
    for name in TOOL_NAMES:
        entry = scores.get(name, {"score": 0.0})
        payload[name] = {"score": entry.get("score", 0.0), **{k: v for k, v in entry.items() if k != "score"}}
    return json.dumps(payload)


def _llm_double(router_reply: str, answer: str):
    """Stand in for LLMClient.complete across a turn.

    The tool-selection call gets the router JSON; the synthesis call gets the
    answer text. They are told apart by `role`, which the agent passes on every
    call precisely so the two are never confused.
    """

    def _complete(prompt, system=None, max_tokens=None, model=None, role="router", **kwargs):
        if role == "synthesis":
            return answer
        return router_reply

    return _complete


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.e2e
@pytest.mark.usefixtures("_candidate_store")
class TestAgentSmoke:
    """Smoke tests for the agent pipeline with mocked externals."""

    def test_run_returns_answer_with_tool_call(self):
        """A structured-field question runs get_structured_data and the answer
        is assembled from the real store, not from the mock."""
        router = _router_json({"get_structured_data": {"score": 1.0, "field": "full_name"}})

        with patch(
            "agent.agent.llm.complete",
            side_effect=_llm_double(router, "The candidate's name is Ada Lovelace."),
        ):
            answer, history, trajectory = run([], "What is the candidate's name?")

        assert answer, "Agent returned an empty answer"
        assert "Ada Lovelace" in answer

        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"

        assert len(trajectory) == 1
        assert trajectory[0]["tool"] == "get_structured_data"
        # The fixture's name reaching the trajectory proves the tool really ran
        # against the store, rather than the answer coming from the mock alone.
        assert "Ada Lovelace" in trajectory[0]["result_preview"]

    def test_run_no_tool_call(self):
        """When no tool clears the threshold — an out-of-scope question — the
        agent still answers, with no tools run."""
        router = _router_json({})  # every tool 0.0

        with patch(
            "agent.agent.llm.complete",
            side_effect=_llm_double(router, "I can only share professional information."),
        ):
            answer, history, trajectory = run([], "What's their star sign?")

        assert answer, "Agent returned an empty answer"
        assert len(history) == 2
        assert trajectory == []

    def test_run_skill_proficiency_tool(self):
        """A skill question runs get_skill_proficiency and surfaces evidence."""
        router = _router_json({"get_skill_proficiency": {"score": 0.9, "skill": "Python"}})

        with patch(
            "agent.agent.llm.complete",
            side_effect=_llm_double(router, "They have solid Python experience building REST APIs."),
        ):
            answer, _history, trajectory = run([], "How good is the candidate at Python?")

        assert answer, "Agent returned an empty answer"
        assert trajectory[0]["tool"] == "get_skill_proficiency"
        assert "REST APIs" in trajectory[0]["result_preview"]

    def test_run_multiple_tools_concurrently(self):
        """Two tools above the threshold both run in one turn.

        This is the behaviour that distinguishes this agent from single-tool
        routing, so it is worth pinning: a question spanning two sources must
        not silently answer from one.
        """
        router = _router_json({
            "get_structured_data": {"score": 0.9, "field": "availability"},
            "get_skill_proficiency": {"score": 0.7, "skill": "Python"},
        })

        with patch(
            "agent.agent.llm.complete",
            side_effect=_llm_double(router, "Available immediately, and strong in Python."),
        ):
            _answer, _history, trajectory = run([], "Are they available, and how is their Python?")

        assert {t["tool"] for t in trajectory} == {"get_structured_data", "get_skill_proficiency"}
