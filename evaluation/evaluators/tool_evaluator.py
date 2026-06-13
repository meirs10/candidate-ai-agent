"""
Tool Selection Evaluator — compares the agent's tool choices against
the golden dataset's expected_source field.

Metrics:
  - Tool Accuracy: Did the agent pick the correct tool (structured vs docs)?
"""

import pandas as pd


def _classify_actual_tool(trajectory: list[dict]) -> str:
    """Determine the effective tool source from a tool trajectory.

    Returns: "structured", "docs", or "none"
    """
    if not trajectory:
        return "none"

    tool_names = [t["tool"] for t in trajectory]

    # If search_documents was used at any point, the effective source is docs
    if "search_documents" in tool_names:
        return "docs"

    # If only get_structured_data was used
    if "get_structured_data" in tool_names:
        return "structured"

    return "none"


def run_tool_evaluation(data: list[dict]) -> pd.DataFrame:
    """
    Evaluate tool selection for each question.

    Args:
        data: List of pipeline result dicts, each with:
            - question (str)
            - expected_source (str): "structured", "docs", or "none"
            - tool_trajectory (list[dict])

    Returns:
        DataFrame with columns:
            id, question, candidate_id, candidate_name,
            expected_tool, actual_tool, tool_correct, trajectory_summary
    """
    rows = []
    for d in data:
        trajectory = d.get("tool_trajectory", [])
        expected = d["expected_source"]
        actual = _classify_actual_tool(trajectory)

        # Build a short summary of the trajectory
        traj_summary = " → ".join(t["tool"] for t in trajectory) if trajectory else "no tools"

        rows.append({
            "id": d["id"],
            "question": d["question"],
            "candidate_id": d.get("candidate_id", ""),
            "candidate_name": d.get("candidate_name", ""),
            "expected_tool": expected,
            "actual_tool": actual,
            "tool_correct": expected == actual,
            "trajectory_summary": traj_summary,
        })

    df = pd.DataFrame(rows)

    # Print summary
    total = len(df)
    correct = df["tool_correct"].sum()
    print(f"[Tool Eval] Accuracy: {correct}/{total} ({correct/total*100:.1f}%)")

    return df
