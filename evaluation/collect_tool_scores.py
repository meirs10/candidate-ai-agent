"""
collect_tool_scores.py — Fast tool-selection probe for threshold tuning.

Threshold selection only needs the router's per-tool PROBABILITIES, and those do
not depend on retrieval or answer synthesis. So this bypasses the full pipeline
(no ChromaDB, no ingestion, no torch) and just calls the scoring router once per
golden question, then sweeps thresholds to recommend:

  * regular threshold  — maximizes F1 (precision AND recall of tool selection)
  * fallback threshold — the lower "always catch the correct tool" bar

Run:
    python -m evaluation.collect_tool_scores              # collect + analyze
    python -m evaluation.collect_tool_scores --analyze    # re-analyze saved CSV
    python -m evaluation.collect_tool_scores --workers 8  # parallelize the calls

Writes evaluation/reports/tool_scores_probe.csv (question_id, candidate_name,
category, difficulty, expected_source, accept_sources, prob_structured/skill/
docs/project).
"""

from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

# NOTE: import ONLY the router + LLM client — NOT agent.agent / agent.tools,
# which would pull in rag.retriever -> chromadb. The router needs neither.
from agent.llm import LLMClient
from agent.tool_router import score_tools, TOOL_SOURCE, SOURCE_ORDER

_DATA_DIR = Path(__file__).parent / "data"
_REPORTS_DIR = Path(__file__).parent / "reports"
_OUT = _REPORTS_DIR / "tool_scores_probe.csv"

# (dataset dir, display name). Candidate names come from candidate_seed.json.
_CANDIDATE_DIRS = [f"candidate_{i}" for i in range(1, 7)]


def _candidate_name(d: Path) -> str:
    seed = d / "candidate_seed.json"
    if seed.exists():
        try:
            return json.loads(seed.read_text(encoding="utf-8")).get("full_name", d.name)
        except Exception:
            pass
    return d.name


def _load_questions() -> list[dict]:
    """Every golden question across the 6 candidates + the project KB."""
    items = []
    for name in _CANDIDATE_DIRS:
        d = _DATA_DIR / name
        gd = d / "golden_dataset.json"
        if not gd.exists():
            continue
        cname = _candidate_name(d)
        for q in json.loads(gd.read_text(encoding="utf-8")):
            q = dict(q)
            q["candidate_name"] = cname
            items.append(q)
    proj = _DATA_DIR / "project" / "golden_dataset.json"
    if proj.exists():
        for q in json.loads(proj.read_text(encoding="utf-8")):
            q = dict(q)
            q["candidate_name"] = "Project Knowledge Base"
            items.append(q)
    return items


def collect(workers: int = 4) -> pd.DataFrame:
    llm = LLMClient()
    questions = _load_questions()
    print(f"[probe] scoring {len(questions)} questions with {workers} worker(s)...")

    def _score(q):
        scores = score_tools(llm, q["question"])
        return {
            "question_id": q.get("id", ""),
            "candidate_name": q.get("candidate_name", ""),
            "category": q.get("category", ""),
            "difficulty": q.get("difficulty", ""),
            "expected_source": q.get("expected_source", ""),
            "accept_sources": "|".join(q.get("accept_sources") or []),
            "question": q["question"],
            "prob_structured": scores["get_structured_data"]["score"],
            "prob_skill": scores["get_skill_proficiency"]["score"],
            "prob_docs": scores["search_documents"]["score"],
            "prob_project": scores["search_project"]["score"],
        }

    rows = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for i, row in enumerate(pool.map(_score, questions), 1):
            rows.append(row)
            if i % 25 == 0:
                print(f"  [probe] {i}/{len(questions)}")

    df = pd.DataFrame(rows)
    _REPORTS_DIR.mkdir(exist_ok=True)
    df.to_csv(_OUT, index=False)
    print(f"[probe] wrote {_OUT}")
    return df


# --- Threshold analysis ------------------------------------------------------

_SOURCE_TO_PROB = {s: f"prob_{s}" for s in SOURCE_ORDER}  # structured/skill/docs/project


def _correct_set(row) -> set:
    """The source labels that count as correct for a question."""
    acc = {row["expected_source"]} | set(
        str(row.get("accept_sources") or "").split("|")) - {""}
    return {s for s in acc if s}


def analyze(df: pd.DataFrame):
    df = df.copy()
    for c in _SOURCE_TO_PROB.values():
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)

    # Split: questions that SHOULD fire a tool vs negatives ("none").
    correct_sets = [(_correct_set(r)) for _, r in df.iterrows()]
    is_neg = [("none" in cs or not (cs & set(SOURCE_ORDER))) for cs in correct_sets]
    n_pos = sum(1 for x in is_neg if not x)
    n_neg = sum(is_neg)

    print(f"\n[probe] {len(df)} questions: {n_pos} tool-expected, {n_neg} negative/none\n")
    header = f"{'thr':>5} | {'recall':>7} {'precis':>7} {'F1':>6} | {'avg#fired':>9} {'neg_fire':>8}"
    print(header)
    print("-" * len(header))

    best = None
    fallback = None
    for k in range(1, 20):  # 0.05 .. 0.95
        t = k / 20
        tp = fp = fn = 0
        fired_total = 0
        caught = 0            # non-neg questions where >=1 correct tool fired
        neg_fire = 0          # negative questions where any tool fired
        for (_, row), cs, neg in zip(df.iterrows(), correct_sets, is_neg):
            fired = {s for s in SOURCE_ORDER if row[_SOURCE_TO_PROB[s]] >= t}
            fired_total += len(fired)
            if neg:
                if fired:
                    neg_fire += 1
                fp += len(fired)  # any fire on a negative is a false positive
                continue
            good = fired & cs
            tp += len(good)
            fp += len(fired - cs)
            fn += len(cs - fired)
            if good:
                caught += 1
        recall = caught / n_pos if n_pos else 0.0     # "caught the correct tool"
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        avg_fired = fired_total / len(df)
        neg_rate = neg_fire / n_neg if n_neg else 0.0
        print(f"{t:5.2f} | {recall:7.3f} {precision:7.3f} {f1:6.3f} | "
              f"{avg_fired:9.2f} {neg_rate:8.3f}")
        if best is None or f1 > best[1]:
            best = (t, f1, precision, recall)
        # fallback = the LOWEST bar that still catches the correct tool almost
        # always (recall>=0.97) while not firing on negatives (neg_fire<=0.10).
        # The fallback only runs when the regular bar selected nothing, so it must
        # stay above where negatives start firing.
        if fallback is None and recall >= 0.97 and neg_rate <= 0.10:
            fallback = t

    print("\n[probe] SUGGESTIONS (verify - synthetic data):")
    if best:
        print(f"  regular  (max F1)             -> {best[0]:.2f}  "
              f"(F1={best[1]:.3f}, P={best[2]:.3f}, R={best[3]:.3f})")
    if fallback is not None:
        print(f"  fallback (lowest safe recall) -> {fallback:.2f}")
    else:
        print("  fallback: none met recall>=0.97 & neg_fire<=0.10 - inspect the sweep.")
    print("  Set TOOL_SELECT_THRESHOLD (regular) and TOOL_FALLBACK_THRESHOLD in settings.py.")


if __name__ == "__main__":
    args = sys.argv[1:]
    workers = 4
    if "--workers" in args:
        workers = int(args[args.index("--workers") + 1])
    if "--analyze" in args and _OUT.exists():
        df = pd.read_csv(_OUT)
    else:
        df = collect(workers=workers)
    analyze(df)
