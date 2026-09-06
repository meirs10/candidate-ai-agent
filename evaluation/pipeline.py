"""
Headless pipeline wrapper for evaluation.

Provides functions to run the full agent pipeline
without requiring Streamlit or a running server.
"""

import agent.tools as tools_module
from agent.agent import run as agent_run, get_last_tool_scores
import settings as config  # module named `settings` to avoid shadowing the scorer's `config`

# Precedence for reducing a multi-tool trajectory to a single "final_tool": the
# tool that most grounds the answer wins, so retrieval questions still register
# for the gate / RAGAS filters even when several tools ran.
_FINAL_TOOL_PRECEDENCE = (
    "search_documents", "search_project", "get_skill_proficiency", "get_structured_data",
)


def run_agent_answer(question: str) -> tuple[str, list]:
    """Run the full agent with a fresh conversation, return (answer, tool_trajectory)."""
    answer, _, trajectory = agent_run([], question)
    return answer, trajectory


def run_full_pipeline(
    question: str,
    candidate_id: str,
    top_k: int = 3,
) -> dict:
    """
    Run the full agent for a single question and capture all metadata.

    Returns:
        {
            "question": str,
            "contexts": list[str],         # retrieved chunks (if RAG was used)
            "answer": str,                 # from agent
            "tool_trajectory": list[dict], # sequence of tool calls
            "final_tool": str | None,      # last tool used (or None)
            "route": str | None,           # "broad"/"specific" (if RAG was used)
        }
    """
    answer, trajectory = run_agent_answer(question)

    # Per-tool probabilities from the scored router (all four tools).
    tool_scores = get_last_tool_scores()

    # Reduce the (possibly multi-tool) trajectory to one grounding tool.
    ran = {t["tool"] for t in trajectory}
    final_tool = next((name for name in _FINAL_TOOL_PRECEDENCE if name in ran), None)

    # Extract retrieval metadata captured during the agent run
    # (avoids a second retrieval call which would be non-deterministic).
    # Both RAG tools (candidate docs + project docs) populate the same metadata.
    route = None
    contexts = []
    fused_pool = None
    if any(t["tool"] in ("search_documents", "search_project") for t in trajectory):
        retrieval_meta = tools_module.get_last_retrieval_meta()
        route = retrieval_meta.get("route")
        contexts = retrieval_meta.get("chunks", [])
        fused_pool = retrieval_meta.get("fused_pool")

    return {
        "question": question,
        "contexts": contexts,
        "answer": answer,
        "tool_trajectory": trajectory,
        "final_tool": final_tool,
        "route": route,
        "fused_pool": fused_pool,
        "tool_scores": tool_scores,
    }


def set_candidate_id(candidate_id: str):
    """Monkey-patch the agent's CANDIDATE_ID for evaluation."""
    tools_module.CANDIDATE_ID = candidate_id


def restore_candidate_id(original_id: str | None = None):
    """Restore the production CANDIDATE_ID after evaluation."""
    tools_module.CANDIDATE_ID = original_id or config.CANDIDATE_ID


def set_project_id(project_id: str):
    """Monkey-patch the agent's PROJECT_ID so the project KB is evaluated against
    an isolated collection (cleaned up afterwards)."""
    tools_module.PROJECT_ID = project_id


def restore_project_id(original_id: str | None = None):
    """Restore the production PROJECT_ID after evaluation."""
    tools_module.PROJECT_ID = original_id or config.PROJECT_ID
