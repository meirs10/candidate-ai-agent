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

REPORTS_DIR = Path(__file__).parent / "reports"


def select_rag_results(pipeline_results: list[dict]) -> list[dict]:
    """Questions that should enter the RAG quality metrics (RAGAS).

    Single source of truth for the RAG filter so the harness (which scores) and
    the report (which aligns per-question rows to the score DataFrames by index)
    stay in lock-step. Negative/out-of-scope questions are excluded: by design no
    document chunk is relevant to them, so context precision/recall are meaningless
    and were dragging the aggregate down.
    """
    return [
        r for r in pipeline_results
        if r.get("final_tool") in ("search_documents", "search_project")
        and r.get("contexts")
        and r.get("category") != "negative"
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

    # RAGAS means
    ragas_df = eval_results.get("ragas_df")
    if ragas_df is not None:
        metric_cols = [c for c in ragas_df.columns if c not in ("user_input", "response", "retrieved_contexts", "reference")]
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
    _assign_full(eval_results.get("geval_df"), "deepeval_correctness", "answer_correctness")
    _assign_full(eval_results.get("refusal_df"), "classification", "refusal_correct",
                 transform=lambda c: c in ("TP", "TN"))

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

    # RAGAS — ordered subset matching select_rag_results' filter.
    ragas_df = eval_results.get("ragas_df")
    ragas_cols: list[str] = []
    if ragas_df is not None and len(ragas_df) > 0:
        ragas_cols = [c for c in ragas_df.columns
                      if c not in ("user_input", "response", "retrieved_contexts", "reference")]
        rag_pred = (lambda r: r.get("final_tool") in ("search_documents", "search_project")
                    and r.get("contexts") and r.get("category") != "negative")
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
        '<strong>Tool</strong> = tool-selection accuracy · '
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
        hit_rate = ep.get("hit_rate", 0)
        probe_html = f'<div class="summary-stat"><strong style="color:{_score_color(hit_rate)}">{hit_rate*100:.0f}%</strong> Embedding Hit Rate</div>'

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

    overview_cards = _build_overview_section(pipeline_results, eval_results)
    breakdowns = _build_breakdowns(pipeline_results, eval_results)
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
