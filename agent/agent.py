"""
agent.py — Recruiter-facing agent with probabilistic, multi-tool selection.

Flow (one pass, no re-querying):
  1. score_tools() rates every tool 0..1 for the question and supplies its args.
  2. Every tool whose score >= settings.TOOL_SELECT_THRESHOLD is selected — so a
     close call fires more than one tool.
  3. Selected tools run CONCURRENTLY; their outputs are gathered as context.
  4. One synthesis LLM call answers the question from all the gathered context.
     If no tool clears the threshold (e.g. an out-of-scope question), the agent
     answers with no context and refuses/redirects.

The per-tool probabilities are exposed via get_last_tool_scores() so the eval
pipeline can record them.
"""

from concurrent.futures import ThreadPoolExecutor

import settings as config
import agent.tools as tools_module
from agent.tools import execute_tool
from agent.tool_router import score_tools, TOOL_SOURCE, SOURCE_ORDER, TOOL_NAMES
from agent.llm import LLMClient
from rag.retriever import retrieve

llm = LLMClient()

SYNTHESIS_SYSTEM = """You are an AI representative for a job candidate, answering
recruiter questions accurately and professionally.

You are given the recruiter's question and the information retrieved for it — from
the candidate's verified profile, the skill evidence, the candidate's documents,
and/or this system's own documentation. Answer using ONLY that retrieved
information.

Rules:
- Ground every claim in the retrieved information. Never invent facts.
- If the retrieved information does not answer the question — or nothing was
  retrieved — say briefly that you don't have that information. For personal or
  out-of-scope questions (politics, religion, marital status, health, finances,
  etc.), reply that you can only share professional, career-related information —
  without mentioning tools, fields, or how you work internally.
- The skill evidence has NO numeric rating — describe a skill qualitatively from
  the evidence; never state or invent a 1-5 score, stars, or a percentage.
- Be concise and professional. Always answer in the same language the recruiter
  used.
"""

# Per-tool probabilities from the most recent run(), keyed by source label
# (structured/skill/docs/project). Read by the eval pipeline via get_last_tool_scores.
_LAST_TOOL_SCORES: dict = {}


def get_last_tool_scores() -> dict:
    """Return the per-tool probabilities from the most recent run()."""
    return dict(_LAST_TOOL_SCORES)


def _args_for(name: str, entry: dict, question: str = "") -> dict:
    """Build the call arguments for a tool from its router entry.

    The router sometimes scores a search tool above the threshold but returns an
    empty "query" (and escalation builds args for tools the router never wrote a
    query for at all). An empty query reaches the embedding API as an empty
    string, which Voyage rejects outright — the exception escapes run() and the
    whole question is recorded as an error. Fall back to the recruiter's own
    question, which is a sensible search string anyway.
    """
    if name == "get_structured_data":
        return {"field": entry.get("field", "")}
    if name == "get_skill_proficiency":
        return {"skill": entry.get("skill", "")}
    query = (entry.get("query") or "").strip() or question  # search_documents / search_project
    return {"query": query}


def select_tools(user_message: str, history: list | None = None) -> tuple[dict, list, dict]:
    """Score every tool and select which to run, WITHOUT executing them.

    Single threshold: run every tool with score >= TOOL_SELECT_THRESHOLD. If none
    clear it (out-of-scope), nothing is selected and the agent refuses. Missed
    tools are recovered at runtime by escalation in run() (not by a lower bar).

    Returns (tool_scores, selected, scores):
      tool_scores  {source_label: prob} for all four tools (for eval capture)
      selected     ordered list of (tool_name, args) to run
      scores       the raw router output (per-tool score + args) — kept so run()
                   can build args for the remaining tools if it escalates.
    """
    scores = score_tools(llm, user_message, history)
    tool_scores = {TOOL_SOURCE[n]: round(scores[n]["score"], 4) for n in TOOL_NAMES}

    selected = [(n, _args_for(n, scores[n], user_message)) for n in TOOL_NAMES
                if scores[n]["score"] >= config.TOOL_SELECT_THRESHOLD]
    selected.sort(key=lambda na: SOURCE_ORDER.index(TOOL_SOURCE[na[0]]))
    return tool_scores, selected, scores


def _looks_empty(name: str, text: str) -> bool:
    """True when a tool returned no usable content (used to trigger escalation)."""
    t = (text or "").strip()
    if not t:
        return True
    if name == "get_structured_data":
        return t.endswith("Not provided")
    if name == "get_skill_proficiency":
        return any(m in t for m in (
            "No curated skill evidence",
            "was not among the candidate's assessed skills",
            "no supporting passages were retrieved",
        ))
    # search tools
    return t.startswith("No relevant information found")


def _run_one_tool(name: str, args: dict):
    """Execute a single tool. For the search tools we call retrieve() directly so
    each call's metadata is captured locally (thread-safe — no shared global).

    Returns (name, args, text, meta, empty); meta is None for non-search tools,
    empty is True when the tool found nothing usable.
    """
    if name in ("search_documents", "search_project"):
        collection = (tools_module.CANDIDATE_ID if name == "search_documents"
                      else tools_module.PROJECT_ID)
        res = retrieve(str(args.get("query") or ""), collection)
        chunks = res["chunks"]
        if chunks:
            text = "\n\n".join(chunks)
        else:
            text = ("No relevant information found in documents."
                    if name == "search_documents"
                    else "No relevant information found about the project.")
        meta = {"route": res["route"], "expanded_queries": res["expanded_queries"],
                "chunks": chunks, "fused_pool": res.get("fused_pool")}
        return name, args, text, meta, not chunks

    text = execute_tool(name, args)
    return name, args, text, None, _looks_empty(name, text)


def _run_tools_concurrently(pairs: list) -> list:
    """Run a list of (name, args) tools concurrently; return their result tuples."""
    if not pairs:
        return []
    with ThreadPoolExecutor(max_workers=len(pairs)) as pool:
        futures = [pool.submit(_run_one_tool, n, a) for (n, a) in pairs]
        return [f.result() for f in futures]


def _set_retrieval_meta(results: list):
    """Aggregate the search tools' metadata into tools.get_last_retrieval_meta()'s
    backing store so the eval pipeline can capture contexts/route/fused_pool.

    Chunks are the union across search tools (order-preserving, de-duplicated);
    route/fused_pool come from candidate docs when present, else the project search.
    """
    search = [(n, m) for (n, a, t, m, e) in results if m is not None]
    if not search:
        tools_module._last_retrieval_meta = {}
        return
    seen, chunks = set(), []
    for _, m in search:
        for c in m.get("chunks", []):
            if c not in seen:
                seen.add(c)
                chunks.append(c)
    primary = next((m for (n, m) in search if n == "search_documents"), search[0][1])
    tools_module._last_retrieval_meta = {
        "route": primary.get("route"),
        "expanded_queries": primary.get("expanded_queries"),
        "chunks": chunks,
        "fused_pool": primary.get("fused_pool"),
    }


def _synthesize(question: str, history: list, results: list) -> str:
    """One LLM call that answers the question from all gathered tool context."""
    if results:
        context = "\n\n".join(f"[{TOOL_SOURCE[n]}]\n{t}" for (n, a, t, m, e) in results)
    else:
        context = "(no information sources were selected for this question)"

    # Prior turns (exclude the just-appended current user message) for continuity.
    convo = ""
    prior = [m for m in history if m.get("role") in ("user", "assistant")][:-1][-4:]
    if prior:
        convo = ("Recent conversation:\n"
                 + "\n".join(f"{m['role']}: {m.get('content', '')}" for m in prior)
                 + "\n\n")

    prompt = (f"{convo}Recruiter question: {question}\n\n"
              f"Retrieved information:\n{context}\n\n"
              "Answer the question using only the retrieved information above.")
    return llm.complete(prompt, system=SYNTHESIS_SYSTEM, max_tokens=1024, model=llm.agent_model)


def run(conversation_history: list, user_message: str) -> tuple[str, list, list]:
    """
    Main agent turn.

    Scores all tools, runs every tool above the threshold concurrently, and
    synthesizes one grounded answer from the gathered context.

    Returns (answer_text, updated_conversation_history, tool_trajectory), where
    tool_trajectory is a list of
        {"tool", "args", "result_preview", "score"}
    for each tool that actually ran. The full per-tool probability vector (all
    four tools, whether or not they ran) is available via get_last_tool_scores().
    """
    global _LAST_TOOL_SCORES

    conversation_history.append({"role": "user", "content": user_message})

    # 1. Score every tool (one call). 2. Select tools above the threshold.
    _LAST_TOOL_SCORES, selected, scores = select_tools(user_message, conversation_history)

    # 3. Run the selected tools concurrently.
    results = _run_tools_concurrently(selected)

    # 3b. Result-based escalation: if we ran tools but they ALL came back empty,
    # the router likely missed — run the REMAINING tools concurrently and add
    # whatever they retrieve. (Skipped when nothing was selected: that is an
    # out-of-scope question we intend to refuse, not a miss.)
    if (config.TOOL_ESCALATE_ON_EMPTY and results
            and all(empty for (_n, _a, _t, _m, empty) in results)):
        chosen = {n for (n, _a, _t, _m, _e) in results}
        rest = [(n, _args_for(n, scores[n], user_message))
                for n in TOOL_NAMES if n not in chosen]
        results.extend(_run_tools_concurrently(rest))

    # Deterministic order by source precedence (project last-word etc.).
    results.sort(key=lambda r: SOURCE_ORDER.index(TOOL_SOURCE[r[0]]))

    _set_retrieval_meta(results)

    # 4. Synthesize one answer from all gathered context.
    answer = _synthesize(user_message, conversation_history, results)
    conversation_history.append({"role": "assistant", "content": answer})

    trajectory = [{
        "tool": n,
        "args": a,
        "result_preview": (t or "")[:300],
        "score": _LAST_TOOL_SCORES[TOOL_SOURCE[n]],
    } for (n, a, t, m, e) in results]

    return answer, conversation_history, trajectory
