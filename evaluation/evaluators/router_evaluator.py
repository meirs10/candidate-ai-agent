"""
Router Evaluator — checks the RAG query router's broad/specific classification
against the expected_route field in the golden dataset.

Uses the route captured during the agent run (no extra LLM calls).
"""

import pandas as pd


def run_router_evaluation(data: list[dict]) -> pd.DataFrame:
    """
    Evaluate the query router's broad/specific classification.

    Args:
        data: List of pipeline result dicts where expected_source == "docs"
              and expected_route is set. Each must have:
            - id (str)
            - question (str)
            - expected_route (str): "broad" or "specific"
            - route (str | None): actual route from retriever

    Returns:
        DataFrame with columns:
            question_id, candidate_name, category, difficulty, question,
            expected_route, actual_route, route_correct
    """
    rows = []
    for d in data:
        expected_route = d.get("expected_route")
        actual_route = d.get("route")

        # Skip if no expected route or the agent didn't use RAG
        if not expected_route or not actual_route:
            continue

        rows.append({
            "question_id": d["id"],
            "candidate_name": d.get("candidate_name", ""),
            "category": d.get("category", ""),
            "difficulty": d.get("difficulty", ""),
            "question": d["question"],
            "expected_route": expected_route,
            "actual_route": actual_route,
            "route_correct": expected_route == actual_route,
        })

    df = pd.DataFrame(rows)

    if len(df) == 0:
        print("[Router Eval] No router decisions to evaluate (agent may not have used RAG)")
        return df

    # Print summary
    total = len(df)
    correct = df["route_correct"].sum()
    false_broad = len(df[(df["expected_route"] == "specific") & (df["actual_route"] == "broad")])
    false_specific = len(df[(df["expected_route"] == "broad") & (df["actual_route"] == "specific")])

    print(f"[Router Eval] Accuracy: {correct}/{total} ({correct/total*100:.1f}%)")
    print(f"[Router Eval] False-broad (specific -> broad): {false_broad}")
    print(f"[Router Eval] False-specific (broad -> specific): {false_specific}")

    return df
