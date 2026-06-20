"""
Report generator — produces HTML, JSON, or CSV evaluation reports.
Organized by evaluation component.
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
        r
        for r in pipeline_results
        if r.get("final_tool") == "search_documents" and r.get("contexts") and r.get("category") != "negative"
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
    return f"{num / total * 100:.1f}%"


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
      <div class="metric-score" style="color:{_score_color(acc / len(tool_df))}">{_pct(acc, len(tool_df))}</div>
      <div class="metric-label">Tool Accuracy</div>
    </div>"""

    # RAGAS means
    ragas_df = eval_results.get("ragas_df")
    if ragas_df is not None:
        metric_cols = [
            c for c in ragas_df.columns if c not in ("user_input", "response", "retrieved_contexts", "reference")
        ]
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
      <div class="metric-score" style="color:{_score_color(ok / len(gate_df))}">{_pct(ok, len(gate_df))}</div>
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
      <div class="metric-score" style="color:{_score_color(correct / len(router_df))}">{_pct(correct, len(router_df))}</div>
      <div class="metric-label">Router Accuracy</div>
    </div>"""

    return cards


def _build_tool_section(tool_df) -> str:
    """Build the Tool Selection section."""
    if tool_df is None or len(tool_df) == 0:
        return "<p>No tool selection data.</p>"

    total = len(tool_df)
    correct = tool_df["tool_correct"].sum()

    summary = f"""
    <div class="summary-stat"><strong>{correct}/{total}</strong> correct ({_pct(correct, total)})</div>
    """

    rows = ""
    for _, r in tool_df.iterrows():
        color = "#22c55e" if r["tool_correct"] else "#ef4444"
        q = html.escape(str(r["question"])[:60], quote=True)
        rows += f"""
        <tr>
          <td>{r["id"]}</td>
          <td title="{q}">{q}</td>
          <td>{r["expected_tool"]}</td>
          <td style="color:{color}">{r["actual_tool"]}</td>
          <td style="font-size:0.8em">{html.escape(str(r["trajectory_summary"]), quote=True)}</td>
        </tr>"""

    return f"""
    {summary}
    <table>
      <thead><tr><th>ID</th><th>Question</th><th>Expected</th><th>Actual</th><th>Trajectory</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>"""


def _build_rag_section(ragas_df, pipeline_results) -> str:
    """Build the RAG Quality section."""
    if ragas_df is None or len(ragas_df) == 0:
        return "<p>No RAG-routed questions to evaluate.</p>"

    # RAGAS summary
    metric_cols = [
        c for c in ragas_df.columns if c not in ("user_input", "response", "retrieved_contexts", "reference")
    ]
    means_html = ""
    for col in metric_cols:
        vals = ragas_df[col].dropna()
        if len(vals) > 0:
            v = vals.mean()
            means_html += f'<div class="summary-stat"><strong style="color:{_score_color(v)}">{_format_score(v)}</strong> {col.replace("_", " ").title()}</div>'

    # Per-question rows — must use the same selector the harness scored with,
    # so ragas_df.iloc[i] lines up with rag_results[i].
    rag_results = select_rag_results(pipeline_results)
    rows = ""
    for i, r in enumerate(rag_results):
        if i >= len(ragas_df):
            break
        scores = ""
        for col in metric_cols:
            val = ragas_df.iloc[i][col]
            scores += f'<span style="color:{_score_color(val)}" title="{col}">{_format_score(val)}</span> '

        answer = html.escape(str(r["answer"])[:100], quote=True)
        rows += f"""
        <tr>
          <td>{r["id"]}</td>
          <td title="{html.escape(str(r["question"]), quote=True)}">{html.escape(str(r["question"])[:50], quote=True)}</td>
          <td>{r.get("route", "N/A")}</td>
          <td class="answer-cell" title="{answer}">{answer}...</td>
          <td>{scores}</td>
          <td>{r["latency_s"]}s</td>
        </tr>"""

    return f"""
    <p style="color:#94a3b8;margin-bottom:1rem">Showing only questions routed through search_documents ({len(rag_results)} questions)</p>
    {means_html}
    <table>
      <thead><tr><th>ID</th><th>Question</th><th>Route</th><th>Answer</th><th>Scores</th><th>Latency</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>"""


def _build_retrieval_gate_section(gate_df) -> str:
    """Build the Retrieval Gate Localization section (ingestion vs recall vs rerank)."""
    if gate_df is None or len(gate_df) == 0:
        return (
            "<p>No retrieval-gate data. Requires a fresh pipeline run (not REUSE) "
            "so the pre-rerank fused pool is captured.</p>"
        )

    total = len(gate_df)
    stage_color = {"ok": "#22c55e", "rerank": "#eab308", "recall": "#f97316", "ingestion": "#ef4444"}
    counts = gate_df["loss_stage"].value_counts().to_dict()

    summary = ""
    for stage in ("ok", "recall", "rerank", "ingestion"):
        n = counts.get(stage, 0)
        label = "reached answer" if stage == "ok" else f"lost @ {stage}"
        summary += (
            f'<div class="summary-stat"><strong style="color:{stage_color[stage]}">'
            f"{n}</strong> {label} ({_pct(n, total)})</div>"
        )

    rows = ""
    for _, r in gate_df.sort_values("loss_stage").iterrows():
        color = stage_color.get(r["loss_stage"], "#888")
        q = html.escape(str(r["question"])[:55], quote=True)
        rows += f"""
        <tr>
          <td>{r["id"]}</td>
          <td title="{q}">{q}</td>
          <td>{html.escape(str(r.get("candidate_name", "")), quote=True)}</td>
          <td>{r["category"]}</td>
          <td>{_format_score(r["target_sim"])}</td>
          <td style="color:{_score_color(bool(r["in_index"]))}">{_format_score(bool(r["in_index"]))}</td>
          <td style="color:{_score_color(bool(r["in_fused_pool"]))}">{_format_score(bool(r["in_fused_pool"]))}</td>
          <td style="color:{_score_color(bool(r["in_final"]))}">{_format_score(bool(r["in_final"]))}</td>
          <td style="color:{color};font-weight:600">{r["loss_stage"]}</td>
        </tr>"""

    return f"""
    <p style="color:#94a3b8;margin-bottom:1rem">Specific docs questions traced through the retrieval gates.
    <strong>target_sim</strong> = similarity of the best index chunk to the ground-truth answer;
    <strong>loss_stage</strong> = first gate where that chunk was lost
    (ingestion → not well represented in any chunk; recall → never entered the fused pool;
    rerank → cut by the cross-encoder).</p>
    {summary}
    <table>
      <thead><tr><th>ID</th><th>Question</th><th>Candidate</th><th>Category</th>
      <th>target_sim</th><th>In Index</th><th>In Pool</th><th>In Final</th><th>Loss Stage</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>"""


def _build_geval_section(geval_df, pipeline_results) -> str:
    """Build the Answer Correctness (GEval) section."""
    if geval_df is None or len(geval_df) == 0:
        return "<p>No GEval data.</p>"

    vals = geval_df["deepeval_correctness"].dropna()
    mean_val = vals.mean() if len(vals) > 0 else 0

    summary = f'<div class="summary-stat"><strong style="color:{_score_color(mean_val)}">{_format_score(mean_val)}</strong> Mean Correctness ({len(geval_df)} questions)</div>'

    rows = ""
    for i, r in enumerate(pipeline_results):
        if i >= len(geval_df):
            break
        val = geval_df.iloc[i].get("deepeval_correctness")
        answer = html.escape(str(r["answer"])[:100], quote=True)
        gt = html.escape(str(r["ground_truth"])[:100], quote=True)
        rows += f"""
        <tr>
          <td>{r["id"]}</td>
          <td>{r["category"]}</td>
          <td title="{html.escape(str(r["question"]), quote=True)}">{html.escape(str(r["question"])[:50], quote=True)}</td>
          <td class="answer-cell" title="{answer}">{answer}...</td>
          <td class="gt-cell" title="{gt}">{gt}...</td>
          <td style="color:{_score_color(val)}">{_format_score(val)}</td>
        </tr>"""

    return f"""
    {summary}
    <table>
      <thead><tr><th>ID</th><th>Category</th><th>Question</th><th>Answer</th><th>Ground Truth</th><th>Correctness</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>"""


def _build_refusal_section(refusal_df) -> str:
    """Build the Refusal Accuracy section with confusion matrix."""
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
    halluc = refusal_df["hallucinated"].sum()

    # Confusion matrix as HTML table
    cm_html = f"""
    <table style="width:auto;margin:1rem 0">
      <thead>
        <tr><th></th><th>Refused</th><th>Answered</th></tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>Should refuse</strong></td>
          <td style="color:#22c55e">TP = {tp}</td>
          <td style="color:#ef4444">FN = {fn}</td>
        </tr>
        <tr>
          <td><strong>Should answer</strong></td>
          <td style="color:#ef4444">FP = {fp}</td>
          <td style="color:#22c55e">TN = {tn}</td>
        </tr>
      </tbody>
    </table>
    """

    summary = f"""
    <div class="summary-stat"><strong style="color:{_score_color(accuracy)}">{_pct(tp + tn, total)}</strong> Accuracy</div>
    <div class="summary-stat"><strong style="color:{_score_color(precision)}">{precision:.1%}</strong> Precision</div>
    <div class="summary-stat"><strong style="color:{_score_color(recall)}">{recall:.1%}</strong> Recall</div>
    <div class="summary-stat"><strong style="color:{_score_color(1 - halluc / total if total else 1)}">{halluc}</strong> Hallucinations</div>
    {cm_html}
    """

    # Per-question table — show misclassifications first
    sorted_df = refusal_df.sort_values(
        by="classification",
        key=lambda s: s.map({"FP": 0, "FN": 1, "TP": 2, "TN": 3}),
    )

    rows = ""
    for _, r in sorted_df.iterrows():
        cls = r["classification"]
        cls_color = "#22c55e" if cls in ("TP", "TN") else "#ef4444"
        halluc_icon = "⚠️" if r["hallucinated"] else ""
        redir_icon = "✓" if r["professional_redirect"] else ""
        answer = html.escape(str(r["answer_preview"])[:120], quote=True)
        rows += f"""
        <tr>
          <td>{r["id"]}</td>
          <td>{r["category"]}</td>
          <td title="{html.escape(str(r["question"]), quote=True)}">{html.escape(str(r["question"])[:50], quote=True)}</td>
          <td style="color:{cls_color};font-weight:bold">{cls}</td>
          <td>{"Yes" if r["refused"] else "No"}</td>
          <td>{halluc_icon}</td>
          <td>{redir_icon}</td>
          <td class="answer-cell" title="{answer}">{answer}...</td>
        </tr>"""

    return f"""
    {summary}
    <table>
      <thead><tr><th>ID</th><th>Category</th><th>Question</th><th>Class</th><th>Refused</th><th>Halluc</th><th>Redirect</th><th>Answer</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>"""


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
        <div class="summary-stat"><strong>{cs.get("total_chunks", 0)}</strong> Chunks</div>
        <div class="summary-stat"><strong>{cs.get("avg_chunk_size", 0)}</strong> Avg Size</div>
        <div class="summary-stat"><strong>{cs.get("min_chunk_size", 0)}-{cs.get("max_chunk_size", 0)}</strong> Range</div>
        <div class="summary-stat"><strong>{cs.get("empty_or_tiny_chunks", 0)}</strong> Tiny</div>
        """

        # Doc-type breakdown table
        dt_rows = ""
        if dtb:
            for dt, stats in dtb.items():
                dt_rows += f"<tr><td>{dt}</td><td>{stats['chunk_count']}</td><td>{stats['avg_size']}</td><td>{stats['min_size']}</td><td>{stats['max_size']}</td></tr>"
            chunk_html += f"""
            <table style="margin-top:0.5rem">
              <thead><tr><th>Doc Type</th><th>Chunks</th><th>Avg Size</th><th>Min</th><th>Max</th></tr></thead>
              <tbody>{dt_rows}</tbody>
            </table>
            """

        # Section coverage
        coverage_pct = sc.get("coverage_pct", 0)
        missing = sc.get("missing", [])
        section_html = f'<div class="summary-stat"><strong style="color:{_score_color(coverage_pct / 100)}">{coverage_pct}%</strong> Coverage</div>'
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
        probe_html = f'<div class="summary-stat"><strong style="color:{_score_color(hit_rate)}">{hit_rate * 100:.0f}%</strong> Embedding Hit Rate</div>'

        # Duplicates
        dup_html = f"""
        <div class="summary-stat"><strong>{dc.get("exact_duplicates", 0)}</strong> Exact Dups</div>
        <div class="summary-stat"><strong>{dc.get("near_duplicates_sampled", 0)}</strong> Near Dups</div>
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


def _build_router_section(router_df) -> str:
    """Build the Router Accuracy section."""
    if router_df is None or len(router_df) == 0:
        return "<p>No router decisions evaluated.</p>"

    total = len(router_df)
    correct = router_df["route_correct"].sum()
    false_broad = len(router_df[(router_df["expected_route"] == "specific") & (router_df["actual_route"] == "broad")])
    false_specific = len(
        router_df[(router_df["expected_route"] == "broad") & (router_df["actual_route"] == "specific")]
    )

    summary = f"""
    <div class="summary-stat"><strong style="color:{_score_color(correct / total)}">{correct}/{total}</strong> Correct ({_pct(correct, total)})</div>
    <div class="summary-stat"><strong>{false_broad}</strong> False Broad</div>
    <div class="summary-stat"><strong>{false_specific}</strong> False Specific</div>
    """

    rows = ""
    for _, r in router_df.iterrows():
        color = "#22c55e" if r["route_correct"] else "#ef4444"
        q = html.escape(str(r["question"])[:60], quote=True)
        rows += f"""
        <tr>
          <td>{r["id"]}</td>
          <td title="{q}">{q}</td>
          <td>{r["expected_route"]}</td>
          <td style="color:{color}">{r["actual_route"]}</td>
          <td style="color:{color}">{"✓" if r["route_correct"] else "✗"}</td>
        </tr>"""

    return f"""
    {summary}
    <table>
      <thead><tr><th>ID</th><th>Question</th><th>Expected</th><th>Actual</th><th>Correct</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>"""


def _generate_html(pipeline_results, eval_results) -> str:
    """Generate a self-contained component-based HTML report."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    overview_cards = _build_overview_section(pipeline_results, eval_results)
    tool_section = _build_tool_section(eval_results.get("tool_eval_df"))
    rag_section = _build_rag_section(
        eval_results.get("ragas_df"),
        pipeline_results,
    )
    retrieval_gate_section = _build_retrieval_gate_section(eval_results.get("retrieval_gate_df"))
    geval_section = _build_geval_section(eval_results.get("geval_df"), pipeline_results)
    refusal_section = _build_refusal_section(eval_results.get("refusal_df"))
    ingestion_section = _build_ingestion_section(eval_results.get("ingestion_report"))
    router_section = _build_router_section(eval_results.get("router_df"))

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Component-Based Evaluation Report</title>
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
  tr:hover {{ background: #334155; }}
  .answer-cell, .gt-cell {{ max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
  .summary-stat {{ display: inline-block; background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 0.8rem 1.2rem; margin: 0.3rem; }}
  .summary-stat strong {{ color: #38bdf8; }}
  .component-section {{ margin: 2rem 0; padding: 1.5rem; background: #1e293b22; border-radius: 12px; border: 1px solid #334155; }}
</style>
</head>
<body>

<h1>Multi-Candidate Evaluation Report</h1>
<div class="meta">Generated: {timestamp} | Questions: {len(pipeline_results)} | Candidates: {", ".join(sorted(set(r.get("candidate_name", "?") for r in pipeline_results)))}</div>

<h2>Overview</h2>
<div class="metrics-grid">
  {overview_cards}
</div>

<div class="component-section">
<h2>1. Tool Selection</h2>
{tool_section}
</div>

<div class="component-section">
<h2>2. RAG Quality (RAGAS)</h2>
{rag_section}
</div>

<div class="component-section">
<h2>3. Retrieval Gate Localization (Ingestion / Recall / Rerank)</h2>
{retrieval_gate_section}
</div>

<div class="component-section">
<h2>4. Answer Correctness (GEval)</h2>
{geval_section}
</div>

<div class="component-section">
<h2>5. Refusal Accuracy</h2>
{refusal_section}
</div>

<div class="component-section">
<h2>6. Ingestion Quality</h2>
{ingestion_section}
</div>

<div class="component-section">
<h2>7. Router Accuracy</h2>
{router_section}
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
