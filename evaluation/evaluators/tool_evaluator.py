"""
Tool Selection Evaluator — compares the agent's tool choices against
the golden dataset's expected_source field.

Metrics:
  - Tool Accuracy: Did the agent pick the correct tool (structured vs docs)?
"""

import pandas as pd


def _classify_actual_tool(trajectory: list[dict]) -> str:
    """Determine the effective tool source from a tool trajectory.

    Returns: "project", "structured", "skill", "docs", or "none"

    Precedence — the source that actually grounded the answer wins:
      1. project — search_project was used. The project KB is a distinct domain
                   (questions about the system itself), so it is classified first.
      2. docs    — search_documents was used at any point. This deliberately
                   outranks the skill tool so a *fallback* (get_skill_proficiency
                   misses → search_documents) is scored as docs, matching the
                   golden expectation for skills not in the assessed list.
      3. skill   — get_skill_proficiency was used and no document search followed
                   (a proficiency question answered straight from the estimator).
      4. structured — only get_structured_data was used.
    """
    if not trajectory:
        return "none"

    tool_names = [t["tool"] for t in trajectory]

    # search_project grounded the answer (questions about the project itself)
    if "search_project" in tool_names:
        return "project"

    # search_documents grounded the answer (incl. skill-tool → docs fallback)
    if "search_documents" in tool_names:
        return "docs"

    # Proficiency answered by the estimator, no document fallback needed
    if "get_skill_proficiency" in tool_names:
        return "skill"

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
            - expected_source (str): "structured", "skill", "docs", or "none"
            - tool_trajectory (list[dict])

    Returns:
        DataFrame with columns:
            question_id, candidate_name, category, difficulty, question,
            candidate_id, expected_tool, accepted_tools, actual_tool,
            tool_correct, trajectory_summary
    """
    rows = []
    for d in data:
        trajectory = d.get("tool_trajectory", [])
        expected = d["expected_source"]
        actual = _classify_actual_tool(trajectory)

        # Some questions are legitimately answerable by more than one tool — e.g.
        # "Does the candidate have experience with Kubernetes?" when Kubernetes is
        # an assessed skill (both get_skill_proficiency and search_documents are
        # correct). Such questions carry accept_sources; any listed tool counts.
        accepted = {expected} | set(d.get("accept_sources") or [])

        # Build a short summary of the trajectory
        traj_summary = " → ".join(t["tool"] for t in trajectory) if trajectory else "no tools"

        rows.append({
            "question_id": d["id"],
            "candidate_name": d.get("candidate_name", ""),
            "category": d.get("category", ""),
            "difficulty": d.get("difficulty", ""),
            "question": d["question"],
            "candidate_id": d.get("candidate_id", ""),
            "expected_tool": expected,
            "accepted_tools": "|".join(sorted(accepted)),
            "actual_tool": actual,
            "tool_correct": actual in accepted,
            "trajectory_summary": traj_summary,
        })

    df = pd.DataFrame(rows)

    # Print summary
    total = len(df)
    correct = df["tool_correct"].sum()
    print(f"[Tool Eval] Accuracy: {correct}/{total} ({correct/total*100:.1f}%)")

    return df
