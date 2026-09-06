"""
Report generator — produces HTML, JSON, or CSV evaluation reports.

The HTML report is an INSIGHT report: top-line score summary plus score
breakdowns sliced by difficulty, question type (category), and candidate — so
you can see where the system is strong and where it lacks, rather than reading
question-by-question rows. The exhaustive per-question detail lives in the JSON
and CSV reports (and the per-component CSVs the harness writes), which are
unchanged.
"""

import html
import json
from datetime import datetime
from pathlib import Path

import pandas as pd

import settings as config
from agent.tool_router import TOOL_SOURCE  # {"get_structured_data": "structured", ...}

REPORTS_DIR = Path(__file__).parent / "reports"

_SOURCE_TO_PROB_COL = {"structured": "prob_structured", "skill": "prob_skill",
                        "docs": "prob_docs", "project": "prob_project"}

# Columns in the RAGAS frame that are NOT metric scores: the RAGAS sample text
# fields plus the standard per-question identity columns every component CSV now
# carries. Everything else in ragas_df is treated as a numeric metric to average.
_RAGAS_NON_METRIC_COLS = (
    "user_input", "response", "retrieved_contexts", "reference",
    "question_id", "candidate_name", "category", "difficulty",
)


def select_rag_results(pipeline_results: list[dict]) -> list[dict]:
    """Questions that should enter the RAG quality metrics (RAGAS).

    Single source of truth for the RAG filter, used by the harness (which scores)
    and the report (which joins per-question rows back onto the score DataFrame).

    Filters on expected_source in ("docs", "project") — i.e. questions the golden
    dataset actually designed to be answered from retrieved documents/project
    docs. This deliberately excludes structured/skill-expected questions even
    when search_documents also fired as part of the multi-tool selection: RAGAS
    would then score that incidental, irrelevant-by-design context against a
    reference that was never meant to come from retrieval (e.g. a 'preferences'
    question whose answer is the structured work_type field — the agent
    correctly answers it from get_structured_data, but if search_documents also
    ran, its unrelated CV chunks would tank context_recall/precision/relevancy
    for a question RAG was never supposed to answer). Negative/out-of-scope
    questions are excluded too (their expected_source is "none").
    """
    return [
        r for r in pipeline_results
        if r.get("expected_source") in ("docs", "project")
        and r.get("contexts")
    ]


def _score_color(score) -> str:
    """Return CSS color for a metric score."""
    if score is None or (isinstance(score, float) and pd.isna(score)):
        return "#888"
    if isinstance(score, bool):
        return "#22c55e" if score else "#ef4444"
    if score >= 0.8:
        return "#22c55e"
    if score >= 0.5:
        return "#eab308"
    return "#ef4444"


def _format_score(score) -> str:
    """Format a score for display."""
    if score is None or (isinstance(score, float) and pd.isna(score)):
        return "N/A"
    if isinstance(score, bool):
        return "✓" if score else "✗"
    return f"{score:.3f}"


def _pct(num, total) -> str:
    """Format a percentage."""
    if total == 0:
        return "N/A"
    return f"{num/total*100:.1f}%"


# ── Tool-selection recomputation (recall-style, with diagnostics) ────────────
#
# The raw 'tool_correct' column in tool_eval_df is PRECEDENCE-based: it reduces
# a (possibly multi-tool) trajectory to one 'actual_tool' and checks that against
# the accepted set. Since the agent deliberately runs several tools when several
# are relevant, a correct tool that ran alongside a higher-precedence one gets
# marked wrong even though its context reached the answer. This recomputes
# tool-selection success as RECALL — "did any accepted tool run, whether picked
# up front (score >= threshold) or added later via escalation" — which is what
# the multi-tool design is actually optimizing for, and derives the selection
# diagnostics (initial vs escalation catches, threshold misses, escalation
# yield, tools/prompt) from the same per-question reconstruction.


def _parse_accepted(accepted_str) -> set[str]:
    return {t for t in str(accepted_str or "").split("|") if t}


def _parse_trajectory_sources(traj_str) -> set[str]:
    """trajectory_summary like 'get_structured_data -> search_documents' or
    'no tools' → the set of source labels (structured/skill/docs/project) that
    actually ran."""
    s = str(traj_str or "").strip()
    if not s or s == "no tools":
        return set()
    names = [n.strip() for n in s.split("->")]
    return {TOOL_SOURCE[n] for n in names if n in TOOL_SOURCE}


def _recompute_tool_selection(tool_df: pd.DataFrame) -> tuple[pd.Series, dict]:
    """Recompute tool-selection correctness as recall (see module note above).

    Returns (recomputed_correct, stats) where recomputed_correct is a bool
    Series aligned to tool_df.index, and stats is the diagnostics dict for the
    Tool Selection Diagnostics report section. If the probability columns are
    missing (an older report), the original 'tool_correct' column is kept
    unchanged and stats is empty.
    """
    n = len(tool_df)
    prob_cols_present = all(c in tool_df.columns for c in _SOURCE_TO_PROB_COL.values())
    if n == 0 or not prob_cols_present:
        correct = (tool_df["tool_correct"].astype(bool) if "tool_correct" in tool_df.columns
                   else pd.Series([], dtype=bool))
        return correct, {}

    threshold = config.TOOL_SELECT_THRESHOLD
    correct_final, correct_prob, stage = [], [], []
    escalation_fired, escalation_needed, n_tools_ran = [], [], []
    # "avg score of the correct tool" / "below threshold" only apply to
    # tool-expected questions — a negative question has no correct tool to score.

    for _, r in tool_df.iterrows():
        accepted = _parse_accepted(r.get("accepted_tools"))
        probs = {s: float(r.get(col) or 0.0) for s, col in _SOURCE_TO_PROB_COL.items()}
        initial = {s for s, v in probs.items() if v >= threshold}
        ran = _parse_trajectory_sources(r.get("trajectory_summary"))
        n_tools_ran.append(len(ran))

        fired = len(ran) > len(initial)  # escalation adds tools beyond the initial pick
        escalation_fired.append(fired)

        # "none" is the sentinel for out-of-scope questions: correct means NO
        # tool ran, not a literal tool named "none" — the set-intersection check
        # below never matches that string against a real tool name, so handle it
        # separately (matches _classify_actual_tool's "none" semantics).
        wants_none = accepted == {"none"}
        if wants_none:
            caught_initial = not initial
            caught_after = not ran
        else:
            caught_initial = bool(initial & accepted)
            caught_after = bool(ran & accepted)
        needed = not caught_initial  # the initial pick alone would have missed it
        escalation_needed.append(needed)

        if caught_initial:
            stage.append("initial")
        elif fired and caught_after:
            stage.append("escalation")
        else:
            stage.append("missed")

        correct_final.append(caught_after)
        if not wants_none:
            correct_prob.append(max((probs[s] for s in accepted if s in probs), default=0.0))

    correct_series = pd.Series(correct_final, index=tool_df.index)

    fired_needed = sum(1 for f, nd in zip(escalation_fired, escalation_needed) if f and nd)
    fired_not_needed = sum(1 for f, nd in zip(escalation_fired, escalation_needed) if f and not nd)

    n_expected = len(correct_prob)  # tool-expected questions only (excludes negatives)
    stats = {
        "n": n,
        "n_tool_expected": n_expected,
        "threshold": threshold,
        "accuracy": sum(correct_final) / n,
        "avg_correct_prob": (sum(correct_prob) / n_expected) if n_expected else 0.0,
        "below_threshold_pct": (sum(1 for cp in correct_prob if cp < threshold) / n_expected) if n_expected else 0.0,
        "caught_initial": stage.count("initial"),
        "caught_escalation": stage.count("escalation"),
        "missed": stage.count("missed"),
        "escalations_fired": sum(escalation_fired),
        "escalations_needed_and_fired": fired_needed,
        "escalations_not_needed_but_fired": fired_not_needed,
        "avg_tools_per_prompt": sum(n_tools_ran) / n,
    }
    return correct_series, stats


def _apply_tool_recompute(eval_results: dict) -> tuple[dict, dict]:
    """Return a shallow-copied eval_results with tool_eval_df's 'tool_correct'
    replaced by the recall-style value (see _recompute_tool_selection), plus the
    diagnostics stats dict for the Tool Selection Diagnostics section. Every
    downstream reader of tool_eval_df / tool_correct — the overview card, the
    regime breakdowns — picks this up automatically since they just read the
    column.
    """
    tool_df = eval_results.get("tool_eval_df")
    if tool_df is None or len(tool_df) == 0:
        return eval_results, {}

    recomputed, stats = _recompute_tool_selection(tool_df)
    new_tool_df = tool_df.copy()
    new_tool_df["tool_correct"] = recomputed

    eval_results = dict(eval_results)
    eval_results["tool_eval_df"] = new_tool_df
    return eval_results, stats


def _build_tool_selection_section(stats: dict) -> str:
    """Tool Selection Diagnostics: how selection + escalation actually behaved."""
    if not stats:
        return ("<p>No tool-selection probability data in this report "
                "(older report, or prob_* columns missing).</p>")

    n = stats["n"]
    thr = stats["threshold"]

    top = f"""
    <div class="summary-stat"><strong style="color:{_score_color(stats['accuracy'])}">{stats['accuracy']*100:.1f}%</strong> Accuracy (recall-style — any accepted tool ran)</div>
    <div class="summary-stat"><strong style="color:{_score_color(stats['avg_correct_prob'])}">{stats['avg_correct_prob']:.3f}</strong> Avg score of the correct tool</div>
    <div class="summary-stat"><strong style="color:{_score_color(1 - stats['below_threshold_pct'])}">{stats['below_threshold_pct']*100:.1f}%</strong> Correct tool scored below threshold ({thr:.2f})</div>
    <div class="summary-stat"><strong style="color:#38bdf8">{stats['avg_tools_per_prompt']:.2f}</strong> Avg tools called per prompt</div>
    """

    caught_rows = f"""
    <table style="width:auto;margin:1rem 0">
      <thead><tr><th>Caught at</th><th>N</th><th>% of all questions</th></tr></thead>
      <tbody>
        <tr><td>Initial selection (score ≥ {thr:.2f})</td><td>{stats['caught_initial']}</td><td>{_pct(stats['caught_initial'], n)}</td></tr>
        <tr><td>Escalation (result-based retry)</td><td>{stats['caught_escalation']}</td><td>{_pct(stats['caught_escalation'], n)}</td></tr>
        <tr><td style="color:#ef4444">Missed entirely</td><td style="color:#ef4444">{stats['missed']}</td><td style="color:#ef4444">{_pct(stats['missed'], n)}</td></tr>
      </tbody>
    </table>"""

    esc_total = stats["escalations_fired"]
    esc_needed = stats["escalations_needed_and_fired"]
    esc_not_needed = stats["escalations_not_needed_but_fired"]
    esc_html = f"""
    <p style="color:#94a3b8;margin:0.5rem 0">Escalation fires when every initially-selected tool comes back empty,
    and runs the remaining tools as a safety net. "Needed" = the initial selection would have missed the
    right tool anyway; "not needed" = the right tool was already selected but returned nothing (e.g. a genuine
    no-data case), so escalation ran without changing the outcome.</p>
    <div class="summary-stat"><strong style="color:#38bdf8">{esc_total}</strong> Escalations fired ({_pct(esc_total, n)} of questions)</div>
    <div class="summary-stat"><strong style="color:#22c55e">{esc_needed}</strong> …needed ({_pct(esc_needed, esc_total)} of escalations)</div>
    <div class="summary-stat"><strong style="color:#eab308">{esc_not_needed}</strong> …not needed ({_pct(esc_not_needed, esc_total)} of escalations)</div>
    """

    return f"{top}{caught_rows}{esc_html}"


def _filter_ragas_df(ragas_df, pipeline_results: list[dict]):
    """Restrict ragas_df to questions select_rag_results() actually wants
    (expected_source in docs/project), via a key lookup on (candidate_name,
    question_id) against pipeline_results (which carries expected_source;
    ragas_df itself does not). This is the shared filter used by both the
    overview cards and the regime breakdowns, so a structured/skill-expected
    question whose incidental search_documents call happened to get RAGAS-
    scored (e.g. a 'preferences' question answered from structured data) is
    excluded everywhere in the report, not just some of it.

    Falls back to returning ragas_df unchanged when it lacks identity columns
    (a legacy report saved before question_id/candidate_name were added).
    """
    if ragas_df is None or len(ragas_df) == 0:
        return ragas_df
    rcols = set(ragas_df.columns)
    rid = "question_id" if "question_id" in rcols else ("id" if "id" in rcols else None)
    if not (rid and "candidate_name" in rcols):
        return ragas_df
    expected_map = {(r.get("candidate_name"), r.get("id")): r.get("expected_source")
                    for r in pipeline_results}
    mask = [expected_map.get((cn, i)) in ("docs", "project")
            for cn, i in zip(ragas_df["candidate_name"], ragas_df[rid])]
    return ragas_df[mask]


# ── Top-line overview cards ──────────────────────────────────────────────────


def _build_overview_section(pipeline_results, eval_results) -> str:
    """Build the overview section with summary cards."""
    total = len(pipeline_results)
    avg_latency = round(sum(r["latency_s"] for r in pipeline_results) / total, 2) if total else 0

    # Count unique candidates
    candidate_names = set(r.get("candidate_name", "?") for r in pipeline_results)
    num_candidates = len(candidate_names)

    cards = f"""
    <div class="metric-card">
      <div class="metric-score" style="color:#38bdf8">{num_candidates}</div>
      <div class="metric-label">Candidates</div>
    </div>
    <div class="metric-card">
      <div class="metric-score" style="color:#38bdf8">{total}</div>
      <div class="metric-label">Total Questions</div>
    </div>
    <div class="metric-card">
      <div class="metric-score" style="color:#38bdf8">{avg_latency}s</div>
      <div class="metric-label">Avg Latency</div>
    </div>"""

    # Tool selection accuracy
    tool_df = eval_results.get("tool_eval_df")
    if tool_df is not None and len(tool_df) > 0:
        acc = tool_df["tool_correct"].sum()
        cards += f"""
    <div class="metric-card">
      <div class="metric-score" style="color:{_score_color(acc/len(tool_df))}">{_pct(acc, len(tool_df))}</div>
      <div class="metric-label">Tool Accuracy</div>
    </div>"""

    # RAGAS means — filtered to expected_source in docs/project (see
    # _filter_ragas_df) so structured/skill-expected questions whose incidental
    # search_documents call got RAGAS-scored don't drag these top-line cards down.
    ragas_df = _filter_ragas_df(eval_results.get("ragas_df"), pipeline_results)
    if ragas_df is not None and len(ragas_df) > 0:
        metric_cols = [c for c in ragas_df.columns if c not in _RAGAS_NON_METRIC_COLS]
        for col in metric_cols:
            vals = ragas_df[col].dropna()
            if len(vals) > 0:
                mean_val = vals.mean()
                label = col.replace("_", " ").title()
                cards += f"""
    <div class="metric-card">
      <div class="metric-score" style="color:{_score_color(mean_val)}">{_format_score(mean_val)}</div>
      <div class="metric-label">RAG: {label}</div>
    </div>"""

    # GEval mean
    geval_df = eval_results.get("geval_df")
    if geval_df is not None and "deepeval_correctness" in geval_df.columns:
        vals = geval_df["deepeval_correctness"].dropna()
        if len(vals) > 0:
            mean_val = vals.mean()
            cards += f"""
    <div class="metric-card">
      <div class="metric-score" style="color:{_score_color(mean_val)}">{_format_score(mean_val)}</div>
      <div class="metric-label">Answer Correctness</div>
    </div>"""

    # Retrieval gate — share of specific docs questions whose relevant chunk reached
    # the final context (i.e. retrieval did not drop it).
    gate_df = eval_results.get("retrieval_gate_df")
    if gate_df is not None and len(gate_df) > 0:
        ok = (gate_df["loss_stage"] == "ok").sum()
        cards += f"""
    <div class="metric-card">
      <div class="metric-score" style="color:{_score_color(ok/len(gate_df))}">{_pct(ok, len(gate_df))}</div>
      <div class="metric-label">Retrieval Reaches Answer</div>
    </div>"""

    # Refusal accuracy
    refusal_df = eval_results.get("refusal_df")
    if refusal_df is not None and len(refusal_df) > 0:
        tp = (refusal_df["classification"] == "TP").sum()
        tn = (refusal_df["classification"] == "TN").sum()
        acc = (tp + tn) / len(refusal_df)
        cards += f"""
    <div class="metric-card">
      <div class="metric-score" style="color:{_score_color(acc)}">{_pct(tp + tn, len(refusal_df))}</div>
      <div class="metric-label">Refusal Accuracy</div>
    </div>"""

    # Router accuracy
    router_df = eval_results.get("router_df")
    if router_df is not None and len(router_df) > 0:
        correct = router_df["route_correct"].sum()
        cards += f"""
    <div class="metric-card">
      <div class="metric-score" style="color:{_score_color(correct/len(router_df))}">{_pct(correct, len(router_df))}</div>
      <div class="metric-label">Router Accuracy</div>
    </div>"""

    return cards


# ── Merged per-question score frame (the basis for every breakdown) ──────────


def _build_merged_df(pipeline_results, eval_results) -> tuple[pd.DataFrame, list[str]]:
    """Join every component's per-question score back onto the question's regime
    metadata (difficulty / category / candidate).

    IMPORTANT: question ids are only unique *within* a candidate (every candidate
    reuses p001/q001/…), so a join by bare id collapses all candidates onto one
    set of scores. We therefore align by POSITION — exactly how each evaluator
    produced its rows: over the full ordered question list (tool/refusal/GEval),
    or over an ordered subset it filtered to (router by expected_route, RAGAS by
    select_rag_results). The retrieval-gate frame carries candidate_name, so it is
    joined on the composite (candidate_name, id) key.

    Returns (merged_df, ragas_metric_cols).
    """
    base = pd.DataFrame([{
        "id": r.get("id"),
        "category": r.get("category", "?"),
        "difficulty": r.get("difficulty", "?"),
        "candidate_name": r.get("candidate_name", "?"),
        "latency_s": r.get("latency_s"),
    } for r in pipeline_results])

    if base.empty:
        return base, []

    n = len(base)

    def _assign_full(df, src, dst, transform=None):
        """Position-align a frame scored over the full, ordered question list."""
        if df is not None and len(df) == n and src in getattr(df, "columns", []):
            vals = list(df[src].values)
            base[dst] = [transform(v) if transform else v for v in vals]
        else:
            base[dst] = pd.NA

    def _assign_subset(df, src, dst, predicate, transform=None):
        """Position-align a frame scored over an ordered subset, re-deriving that
        subset with the same per-row predicate the harness filtered on."""
        vals = [pd.NA] * n
        if df is not None and src in getattr(df, "columns", []):
            idx = 0
            for i, r in enumerate(pipeline_results):
                if predicate(r):
                    if idx < len(df):
                        v = df.iloc[idx][src]
                        vals[i] = transform(v) if transform else v
                    idx += 1
        base[dst] = vals

    # Full, ordered: these evaluators score every question, in pipeline order.
    _assign_full(eval_results.get("tool_eval_df"), "tool_correct", "tool_correct")
    _assign_full(eval_results.get("refusal_df"), "classification", "refusal_correct",
                 transform=lambda c: c in ("TP", "TN"))

    # Ordered subset: GEval excludes negative (out-of-scope) questions.
    _assign_subset(eval_results.get("geval_df"), "deepeval_correctness", "answer_correctness",
                   predicate=lambda r: r.get("category") != "negative")

    # Ordered subset: router scored only questions that carry an expected_route.
    _assign_subset(eval_results.get("router_df"), "route_correct", "route_correct",
                   predicate=lambda r: r.get("expected_route") is not None)

    # Retrieval gate carries candidate_name → join on the composite key (ids alone
    # are ambiguous across candidates).
    gate_df = eval_results.get("retrieval_gate_df")
    gate_cols = set(getattr(gate_df, "columns", []))
    # The id column is "question_id" (current) or "id" (older reports).
    gid = "question_id" if "question_id" in gate_cols else "id"
    if (gate_df is not None
            and {gid, "candidate_name", "loss_stage"} <= gate_cols):
        gmap = {(row["candidate_name"], row[gid]): (row["loss_stage"] == "ok")
                for _, row in gate_df.iterrows()}
        base["retrieval_ok"] = [gmap.get((cn, i), pd.NA)
                                for cn, i in zip(base["candidate_name"], base["id"])]
    else:
        base["retrieval_ok"] = pd.NA

    # RAGAS — filtered to questions select_rag_results() actually wants (see
    # _filter_ragas_df), then key-joined on (candidate_name, question_id). A key
    # join is used — rather than re-deriving a predicate and position-matching
    # it against ragas_df's row order — because the CSV now carries real
    # identity columns, and because a saved ragas_df from before this fix may
    # include structured/skill-expected rows that must be OMITTED, not
    # repositioned: re-deriving today's predicate over pipeline_results and
    # aligning by position would silently misalign those rows onto the wrong
    # scores instead of dropping them.
    ragas_df = _filter_ragas_df(eval_results.get("ragas_df"), pipeline_results)
    ragas_cols: list[str] = []
    if ragas_df is not None and len(ragas_df) > 0:
        ragas_cols = [c for c in ragas_df.columns if c not in _RAGAS_NON_METRIC_COLS]
        rcols = set(ragas_df.columns)
        rid = "question_id" if "question_id" in rcols else ("id" if "id" in rcols else None)
        if rid and "candidate_name" in rcols:
            rmap = {(row["candidate_name"], row[rid]): row for _, row in ragas_df.iterrows()}
            for col in ragas_cols:
                base[col] = [rmap[(cn, i)][col] if (cn, i) in rmap else pd.NA
                            for cn, i in zip(base["candidate_name"], base["id"])]
        else:
            # Legacy CSV without identity columns — fall back to positional
            # alignment (only correct if this ragas_df was produced by exactly
            # today's select_rag_results predicate).
            rag_pred = (lambda r: r.get("expected_source") in ("docs", "project")
                        and r.get("contexts"))
            for col in ragas_cols:
                _assign_subset(ragas_df, col, col, predicate=rag_pred)

    # Coerce every metric column to numeric (bools → 1/0, missing → NaN) so the
    # group means are well-defined.
    metric_cols = ["tool_correct", "route_correct", "refusal_correct",
                   "retrieval_ok", "answer_correctness"] + ragas_cols
    for col in metric_cols:
        if col in base.columns:
            base[col] = pd.to_numeric(base[col], errors="coerce")

    return base, ragas_cols


def _metric_specs(ragas_cols: list[str]) -> list[tuple[str, str]]:
    """(column, header label) for every score column shown in the breakdowns."""
    specs = [
        ("tool_correct", "Tool"),
        ("answer_correctness", "Answer"),
        ("route_correct", "Router"),
        ("refusal_correct", "Refusal"),
        ("retrieval_ok", "Retrieval"),
    ]
    specs += [(c, c.replace("_", " ").title()) for c in ragas_cols]
    return specs


def _mean_cell(series: pd.Series) -> str:
    """A colored percentage cell for the mean of an applicable-only score column."""
    vals = series.dropna()
    if len(vals) == 0:
        return '<td style="color:#475569">—</td>'
    m = float(vals.mean())
    return f'<td style="color:{_score_color(m)};font-weight:600">{m*100:.0f}%</td>'


def _breakdown_table(merged: pd.DataFrame, group_col: str, group_label: str,
                     ragas_cols: list[str], order: list[str] | None = None) -> str:
    """Render one breakdown table: rows = regime values, cols = mean of each
    metric (+ N and mean latency), with an aggregate 'All' row."""
    if merged.empty or group_col not in merged.columns:
        return "<p>No data.</p>"

    specs = _metric_specs(ragas_cols)
    present = [g for g in merged[group_col].dropna().unique().tolist()]
    if order:
        groups = [g for g in order if g in present]
        groups += sorted((g for g in present if g not in order), key=str)
    else:
        groups = sorted(present, key=str)

    header = (f"<th>{group_label}</th><th>N</th>"
              + "".join(f"<th>{lbl}</th>" for _, lbl in specs)
              + "<th>Latency</th>")

    body = ""
    for g in groups + ["__ALL__"]:
        is_all = g == "__ALL__"
        sub = merged if is_all else merged[merged[group_col] == g]
        name = "All" if is_all else str(g)
        cells = "".join(_mean_cell(sub[col]) for col, _ in specs)
        lat = sub["latency_s"].dropna()
        lat_cell = f"<td>{lat.mean():.2f}s</td>" if len(lat) else "<td>—</td>"
        style = ' style="font-weight:700;background:#0f172a"' if is_all else ""
        body += (f"<tr{style}><td>{html.escape(name)}</td><td>{len(sub)}</td>"
                 f"{cells}{lat_cell}</tr>")

    return f"""
    <table>
      <thead><tr>{header}</tr></thead>
      <tbody>{body}</tbody>
    </table>"""


def _build_breakdowns(pipeline_results, eval_results) -> str:
    """The three insight tables: by difficulty, by question type, by candidate."""
    merged, ragas_cols = _build_merged_df(pipeline_results, eval_results)
    if merged.empty:
        return "<p>No questions to summarize.</p>"

    legend = (
        '<p style="color:#94a3b8;margin:0.5rem 0 1rem">Each cell is the mean score '
        'over the <em>applicable</em> questions in that group (— = metric does not '
        'apply to any question there). '
        '<strong>Tool</strong> = tool-selection accuracy (recall-style: any accepted '
        'tool ran, whether via the initial threshold or escalation — see Tool '
        'Selection Diagnostics below) · '
        '<strong>Answer</strong> = GEval answer correctness · '
        '<strong>Router</strong> = broad/specific routing accuracy · '
        '<strong>Refusal</strong> = refusal confusion accuracy · '
        '<strong>Retrieval</strong> = share of specific-doc questions whose evidence '
        'reached the final context · RAGAS metrics are over RAG-routed questions.</p>'
    )

    by_difficulty = _breakdown_table(
        merged, "difficulty", "Difficulty", ragas_cols,
        order=["easy", "medium", "hard"])
    by_category = _breakdown_table(
        merged, "category", "Question Type", ragas_cols)
    by_candidate = _breakdown_table(
        merged, "candidate_name", "Candidate", ragas_cols)

    return f"""
    {legend}
    <h3 style="color:#cbd5e1;margin-top:1.5rem">By Difficulty</h3>
    {by_difficulty}
    <h3 style="color:#cbd5e1;margin-top:1.5rem">By Question Type</h3>
    {by_category}
    <h3 style="color:#cbd5e1;margin-top:1.5rem">By Candidate</h3>
    {by_candidate}"""


# ── Diagnostic summaries (no per-question rows) ──────────────────────────────


def _build_refusal_summary(refusal_df) -> str:
    """Confusion matrix + precision/recall summary (no per-question table)."""
    if refusal_df is None or len(refusal_df) == 0:
        return "<p>No refusal data.</p>"

    tp = (refusal_df["classification"] == "TP").sum()
    tn = (refusal_df["classification"] == "TN").sum()
    fp = (refusal_df["classification"] == "FP").sum()
    fn = (refusal_df["classification"] == "FN").sum()
    total = len(refusal_df)
    accuracy = (tp + tn) / total if total > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    halluc = refusal_df["hallucinated"].sum() if "hallucinated" in refusal_df.columns else 0

    cm_html = f"""
    <table style="width:auto;margin:1rem 0">
      <thead><tr><th></th><th>Refused</th><th>Answered</th></tr></thead>
      <tbody>
        <tr><td><strong>Should refuse</strong></td>
          <td style="color:#22c55e">TP = {tp}</td>
          <td style="color:#ef4444">FN = {fn}</td></tr>
        <tr><td><strong>Should answer</strong></td>
          <td style="color:#ef4444">FP = {fp}</td>
          <td style="color:#22c55e">TN = {tn}</td></tr>
      </tbody>
    </table>"""

    return f"""
    <div class="summary-stat"><strong style="color:{_score_color(accuracy)}">{_pct(tp + tn, total)}</strong> Accuracy</div>
    <div class="summary-stat"><strong style="color:{_score_color(precision)}">{precision:.1%}</strong> Precision</div>
    <div class="summary-stat"><strong style="color:{_score_color(recall)}">{recall:.1%}</strong> Recall</div>
    <div class="summary-stat"><strong style="color:{_score_color(1 - halluc/total if total else 1)}">{halluc}</strong> Hallucinations</div>
    {cm_html}"""


def _build_retrieval_gate_summary(gate_df) -> str:
    """Loss-stage distribution overall and broken down by candidate (where was the
    evidence lost: recall, rerank, or not well chunked at ingestion)."""
    if gate_df is None or len(gate_df) == 0:
        return ("<p>No retrieval-gate data. Requires a fresh pipeline run (not REUSE) "
                "so the pre-rerank fused pool is captured.</p>")

    total = len(gate_df)
    stage_color = {"ok": "#22c55e", "rerank": "#eab308", "recall": "#f97316", "ingestion": "#ef4444"}
    counts = gate_df["loss_stage"].value_counts().to_dict()

    summary = ""
    for stage in ("ok", "recall", "rerank", "ingestion"):
        n = counts.get(stage, 0)
        label = "reached answer" if stage == "ok" else f"lost @ {stage}"
        summary += (f'<div class="summary-stat"><strong style="color:{stage_color[stage]}">'
                    f'{n}</strong> {label} ({_pct(n, total)})</div>')

    # Per-candidate breakdown (only if the column is present).
    table = ""
    if "candidate_name" in gate_df.columns:
        rows = ""
        for cand in sorted(gate_df["candidate_name"].dropna().unique(), key=str):
            sub = gate_df[gate_df["candidate_name"] == cand]
            c = sub["loss_stage"].value_counts().to_dict()
            ok = c.get("ok", 0)
            ok_pct = ok / len(sub) if len(sub) else 0
            rows += (f"<tr><td>{html.escape(str(cand))}</td><td>{len(sub)}</td>"
                     f'<td style="color:{_score_color(ok_pct)};font-weight:600">{ok_pct*100:.0f}%</td>'
                     f'<td>{c.get("recall", 0)}</td><td>{c.get("rerank", 0)}</td>'
                     f'<td>{c.get("ingestion", 0)}</td></tr>')
        table = f"""
        <table style="margin-top:1rem">
          <thead><tr><th>Candidate</th><th>N</th><th>Reaches Answer</th>
          <th>Lost @ Recall</th><th>Lost @ Rerank</th><th>Lost @ Ingestion</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>"""

    return f"""
    <p style="color:#94a3b8;margin-bottom:1rem">Specific-doc questions traced through the retrieval gates —
    where the ground-truth evidence chunk was first lost
    (ingestion → not well represented in any chunk; recall → never entered the fused pool;
    rerank → cut by the cross-encoder).</p>
    {summary}
    {table}"""


def _build_ingestion_section(ingestion_report) -> str:
    """Build the Ingestion Quality section for multiple candidates."""
    if not ingestion_report:
        return "<p>No ingestion data.</p>"

    # If it's a single-candidate report (legacy), wrap it
    if "chunk_stats" in ingestion_report:
        ingestion_report = {"single": {"name": "Candidate", "report": ingestion_report}}

    sections = ""
    for eval_id, entry in ingestion_report.items():
        name = entry.get("name", eval_id)
        report = entry.get("report", {})

        if "error" in report:
            sections += f'<p style="color:#ef4444">{name}: {report["error"]}</p>'
            continue

        cs = report.get("chunk_stats", {})
        sc = report.get("section_coverage", {})
        dc = report.get("duplicate_check", {})
        sq = report.get("summary_quality", {})
        ep = report.get("embedding_probes", {})
        dtb = report.get("doc_type_breakdown", {})

        # Chunk stats
        chunk_html = f"""
        <div class="summary-stat"><strong>{cs.get('total_chunks', 0)}</strong> Chunks</div>
        <div class="summary-stat"><strong>{cs.get('avg_chunk_size', 0)}</strong> Avg Size</div>
        <div class="summary-stat"><strong>{cs.get('min_chunk_size', 0)}-{cs.get('max_chunk_size', 0)}</strong> Range</div>
        <div class="summary-stat"><strong>{cs.get('empty_or_tiny_chunks', 0)}</strong> Tiny</div>
        """

        # Doc-type breakdown table
        dt_rows = ""
        if dtb:
            for dt, stats in dtb.items():
                dt_rows += f'<tr><td>{dt}</td><td>{stats["chunk_count"]}</td><td>{stats["avg_size"]}</td><td>{stats["min_size"]}</td><td>{stats["max_size"]}</td></tr>'
            chunk_html += f"""
            <table style="margin-top:0.5rem">
              <thead><tr><th>Doc Type</th><th>Chunks</th><th>Avg Size</th><th>Min</th><th>Max</th></tr></thead>
              <tbody>{dt_rows}</tbody>
            </table>
            """

        # Section coverage
        coverage_pct = sc.get("coverage_pct", 0)
        missing = sc.get("missing", [])
        section_html = f'<div class="summary-stat"><strong style="color:{_score_color(coverage_pct/100)}">{coverage_pct}%</strong> Coverage</div>'
        if missing:
            section_html += f'<div class="summary-stat">Missing: {", ".join(missing)}</div>'

        # Summary quality
        sq_score = sq.get("llm_score", 0)
        sq_items = sq.get("checklist_items_found", 0)
        sq_total = sq.get("checklist_total", 5)
        summary_html = f"""
        <div class="summary-stat"><strong style="color:{_score_color(sq_score or 0)}">{_format_score(sq_score)}</strong> Summary</div>
        <div class="summary-stat"><strong>{sq_items}/{sq_total}</strong> Checklist</div>
        """

        # Embedding probes
        # hit_rate is None when the document produced no probe terms — render
        # that as "n/a" rather than a misleading 0%.
        hit_rate = ep.get("hit_rate")
        if hit_rate is None:
            probe_html = ('<div class="summary-stat"><strong>n/a</strong> '
                          'Embedding Hit Rate</div>')
        else:
            probe_html = (f'<div class="summary-stat"><strong style="color:{_score_color(hit_rate)}">'
                          f'{hit_rate*100:.0f}%</strong> Embedding Hit Rate</div>')

        # Duplicates
        dup_html = f"""
        <div class="summary-stat"><strong>{dc.get('exact_duplicates', 0)}</strong> Exact Dups</div>
        <div class="summary-stat"><strong>{dc.get('near_duplicates_sampled', 0)}</strong> Near Dups</div>
        """

        sections += f"""
        <div style="margin:1rem 0;padding:1rem;background:#1e293b;border-radius:8px;border:1px solid #334155">
          <h3 style="color:#f8fafc;font-size:1.1rem;margin-bottom:0.8rem">{html.escape(name)}</h3>
          <h4 style="color:#94a3b8;font-size:0.9rem">Chunks</h4>
          {chunk_html}
          <h4 style="color:#94a3b8;font-size:0.9rem;margin-top:0.8rem">Sections</h4>
          {section_html}
          <h4 style="color:#94a3b8;font-size:0.9rem;margin-top:0.8rem">Summaries</h4>
          {summary_html}
          <h4 style="color:#94a3b8;font-size:0.9rem;margin-top:0.8rem">Embeddings</h4>
          {probe_html}
          <h4 style="color:#94a3b8;font-size:0.9rem;margin-top:0.8rem">Duplicates</h4>
          {dup_html}
        </div>
        """

    return sections


# ── HTML assembly ────────────────────────────────────────────────────────────


def _generate_html(pipeline_results, eval_results) -> str:
    """Generate a self-contained INSIGHT HTML report (summary + breakdowns)."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Recompute tool-selection correctness as recall (see module note above) —
    # this updates the overview card and the regime breakdowns' "Tool" column,
    # and produces the diagnostics for the new Tool Selection section below.
    eval_results, tool_stats = _apply_tool_recompute(eval_results)

    overview_cards = _build_overview_section(pipeline_results, eval_results)
    breakdowns = _build_breakdowns(pipeline_results, eval_results)
    tool_selection_section = _build_tool_selection_section(tool_stats)
    refusal_section = _build_refusal_summary(eval_results.get("refusal_df"))
    retrieval_gate_section = _build_retrieval_gate_summary(eval_results.get("retrieval_gate_df"))
    ingestion_section = _build_ingestion_section(eval_results.get("ingestion_report"))

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Evaluation Insight Report</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    background: #0f172a; color: #e2e8f0;
    padding: 2rem; line-height: 1.6;
  }}
  h1 {{ color: #f8fafc; margin-bottom: 0.5rem; font-size: 1.8rem; }}
  h2 {{ color: #94a3b8; margin: 2rem 0 1rem; font-size: 1.3rem; border-bottom: 1px solid #334155; padding-bottom: 0.5rem; }}
  h3 {{ color: #94a3b8; }}
  .meta {{ color: #64748b; margin-bottom: 2rem; font-size: 0.9rem; }}
  .metrics-grid {{
    display: flex; flex-wrap: wrap; gap: 1rem; margin: 1.5rem 0;
  }}
  .metric-card {{
    background: #1e293b; border: 1px solid #334155; border-radius: 12px;
    padding: 1.2rem 1.5rem; min-width: 140px; text-align: center;
  }}
  .metric-score {{ font-size: 1.6rem; font-weight: 700; }}
  .metric-label {{ font-size: 0.75rem; color: #94a3b8; margin-top: 0.3rem; }}
  table {{
    width: 100%; border-collapse: collapse; margin: 1rem 0;
    background: #1e293b; border-radius: 8px; overflow: hidden;
  }}
  th {{ background: #334155; color: #e2e8f0; padding: 0.75rem 1rem; text-align: left; font-size: 0.85rem; }}
  td {{ padding: 0.6rem 1rem; border-bottom: 1px solid #334155; font-size: 0.85rem; }}
  tr:hover {{ background: #33415555; }}
  .summary-stat {{ display: inline-block; background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 0.8rem 1.2rem; margin: 0.3rem; }}
  .summary-stat strong {{ color: #38bdf8; }}
  .component-section {{ margin: 2rem 0; padding: 1.5rem; background: #1e293b22; border-radius: 12px; border: 1px solid #334155; }}
</style>
</head>
<body>

<h1>Evaluation Insight Report</h1>
<div class="meta">Generated: {timestamp} | Questions: {len(pipeline_results)} | Candidates: {', '.join(sorted(set(r.get('candidate_name', '?') for r in pipeline_results)))}<br>
Per-question detail is in the JSON/CSV reports and the per-component CSVs.</div>

<h2>Overview</h2>
<div class="metrics-grid">
  {overview_cards}
</div>

<div class="component-section">
<h2>Scores by Regime</h2>
{breakdowns}
</div>

<div class="component-section">
<h2>Tool Selection Diagnostics</h2>
{tool_selection_section}
</div>

<div class="component-section">
<h2>Refusal Accuracy</h2>
{refusal_section}
</div>

<div class="component-section">
<h2>Retrieval Gate Localization (Ingestion / Recall / Rerank)</h2>
{retrieval_gate_section}
</div>

<div class="component-section">
<h2>Ingestion Quality</h2>
{ingestion_section}
</div>

</body>
</html>"""
    return html_content


def generate_report(
    pipeline_results: list[dict],
    eval_results: dict,
    output_format: str = "html",
) -> str:
    """
    Generate an evaluation report.

    Args:
        pipeline_results: List of pipeline result dicts
        eval_results: Dict containing all component DataFrames/reports
        output_format: "html", "json", or "csv"

    Returns:
        Path to the generated report file.
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if output_format == "html":
        html_content = _generate_html(pipeline_results, eval_results)
        path = REPORTS_DIR / f"eval_report_{timestamp}.html"
        with open(path, "w", encoding="utf-8") as f:
            f.write(html_content)

    elif output_format == "json":
        # Serialize DataFrames to records
        report_data = {
            "timestamp": timestamp,
            "total_questions": len(pipeline_results),
            "pipeline_results": pipeline_results,
        }
        for key in ["tool_eval_df", "ragas_df", "retrieval_gate_df", "geval_df", "refusal_df", "router_df"]:
            df = eval_results.get(key)
            if df is not None:
                report_data[key.replace("_df", "_scores")] = df.to_dict(orient="records")

        if eval_results.get("ingestion_report"):
            report_data["ingestion_report"] = eval_results["ingestion_report"]

        path = REPORTS_DIR / f"eval_report_{timestamp}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)

    elif output_format == "csv":
        # Merge all results into a single flat table
        df = pd.DataFrame(pipeline_results)
        # Add tool eval columns
        tool_df = eval_results.get("tool_eval_df")
        if tool_df is not None and len(tool_df) == len(df):
            for col in ["actual_tool", "tool_correct", "used_fallback", "missing_fallback"]:
                if col in tool_df.columns:
                    df[col] = tool_df[col].values

        path = REPORTS_DIR / f"eval_report_{timestamp}.csv"
        df.to_csv(path, index=False)

    else:
        raise ValueError(f"Unknown format: {output_format}")

    return str(path)
