"""
Headless pipeline wrapper for evaluation.

Provides functions to run the full agent pipeline
without requiring Streamlit or a running server.
"""

import agent.tools as tools_module
from agent.agent import run as agent_run


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

    final_tool = trajectory[-1]["tool"] if trajectory else None

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
    }


def set_candidate_id(candidate_id: str):
    """Monkey-patch the agent's CANDIDATE_ID for evaluation."""
    tools_module.CANDIDATE_ID = candidate_id


def restore_candidate_id(original_id: str = "candidate_001"):
    """Restore the original CANDIDATE_ID after evaluation."""
    tools_module.CANDIDATE_ID = original_id


def set_project_id(project_id: str):
    """Monkey-patch the agent's PROJECT_ID so the project KB is evaluated against
    an isolated collection (cleaned up afterwards)."""
    tools_module.PROJECT_ID = project_id


def restore_project_id(original_id: str = "project_kb"):
    """Restore the production PROJECT_ID after evaluation."""
    tools_module.PROJECT_ID = original_id
