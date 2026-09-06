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

import re
from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context

import settings as config
import agent.tools as tools_module
from agent import telemetry
from agent.tools import execute_tool
from agent.tool_router import score_tools, TOOL_SOURCE, SOURCE_ORDER, TOOL_NAMES
from agent.llm import LLMClient, AGENT_MAX_TOKENS
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
- Answer directly. Start with the answer itself — never with a preamble about
  where the answer came from. Do not open with "Based on the retrieved
  information", "Based on the candidate's profile", "According to the
  documents", "The retrieved context shows" or any variation. The recruiter
  knows you looked things up; saying so wastes their first line. Write as if you
  simply know the answer.
- Never mention the retrieval, the context, the documents-as-a-mechanism, the
  tools, or your own internal workings — unless the recruiter explicitly asks
  how you work. Citing a source by name when it is genuinely informative ("in
  their write-up of the deraining project") is fine; narrating the lookup is not.
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
    """Run a list of (name, args) tools concurrently; return their result tuples.

    Each task is submitted through a COPY of the calling context so the telemetry
    ContextVar reaches the worker threads. Retrieval makes its own LLM calls
    (query expansion, BROAD/SPECIFIC routing) from inside these workers; without
    this, those calls would find no turn in scope and their cost would vanish
    from the log — silently under-reporting every retrieval question.
    """
    if not pairs:
        return []
    with ThreadPoolExecutor(max_workers=len(pairs)) as pool:
        futures = [pool.submit(copy_context().run, _run_one_tool, n, a)
                   for (n, a) in pairs]
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
    return strip_preamble(
        llm.complete(prompt, system=SYNTHESIS_SYSTEM, max_tokens=AGENT_MAX_TOKENS,
                     model=llm.agent_model, role="synthesis"))


# Belt and braces on the "answer directly" rule above. The instruction alone is
# not reliable: a model asked to ground every claim in retrieved context has a
# strong pull toward announcing that it did, and it opens with "Based on the
# retrieved information..." often enough that a recruiter sees it constantly.
# Prompt-only enforcement failed in testing, so the opener is also stripped
# mechanically. Deliberately narrow: it matches a lead-in phrase followed by a
# comma or colon, never mid-sentence text, so an answer that legitimately says
# "based on" later is untouched.
_PREAMBLE_RE = re.compile(
    r"^\s*(?:"
    r"(?:based (?:up)?on|according to|per|drawing on|from|going by)\s+"
    r"(?:the\s+|their\s+|his\s+|her\s+|this\s+)?"
    r"(?:retrieved\s+|available\s+|provided\s+|supplied\s+)?"
    r"(?:information|context|evidence|材料|documents?|documentation|profile|"
    r"records?|materials?|data|write-?ups?|cv|r[ée]sum[ée]|"
    r"candidate'?s?[^,:.]{0,40})"
    r"[^,:.]{0,60}"
    r")\s*[,:]\s+",
    re.IGNORECASE,
)

# The declarative variant, which carries no comma to anchor on: "The retrieved
# information shows that ...". Separate pattern because allowing the rule above
# to end on plain whitespace would also eat "Based on their PPO work the reward
# function ..." — a genuine, substantive opening.
_PREAMBLE_SHOWS_RE = re.compile(
    r"^\s*(?:the|this)\s+"
    r"(?:retrieved\s+|available\s+|provided\s+)?"
    r"(?:information|context|evidence|documents?|documentation|records?|materials?|data)\s+"
    r"(?:shows?|indicates?|states?|suggests?|confirms?|notes?)"
    r"(?:\s+that)?\s+",
    re.IGNORECASE,
)


def strip_preamble(text: str) -> str:
    """Remove a leading "Based on the retrieved information," style opener.

    Re-capitalises what is left, skipping any Markdown emphasis markers so
    "**diarization**" becomes "**Diarization**" rather than being missed.
    Returns the text unchanged when nothing matches, or when stripping would
    leave nothing at all — an answer that is ONLY a preamble is a stub, but a
    stub still beats a blank reply. Short answers that survive stripping ("Yes,
    immediately.") are kept: brevity is not emptiness.
    """
    stripped = _PREAMBLE_RE.sub("", text, count=1)
    if stripped == text:
        stripped = _PREAMBLE_SHOWS_RE.sub("", text, count=1)
    if stripped == text or not stripped.strip():
        return text
    for i, ch in enumerate(stripped):
        if ch.isalpha():
            return stripped[:i] + ch.upper() + stripped[i + 1:]
        if ch not in "*_`\"'‘“([ ":
            break
    return stripped


def _stream_without_preamble(pieces):
    """Pass a token stream through strip_preamble without stalling it.

    Only the opening is buffered — enough characters to contain any preamble the
    regex could match — and everything after it flows straight through. The delay
    is one short buffer, not the whole answer, so this stays real streaming.
    """
    head = ""
    for piece in pieces:
        if head is None:
            yield piece
            continue
        head += piece
        if len(head) >= 180:
            yield strip_preamble(head)
            head = None
    if head is not None:
        yield strip_preamble(head)


def _synthesis_prompt(question: str, history: list, results: list) -> str:
    """The synthesis prompt, shared by the buffered and streaming paths."""
    if results:
        context = "\n\n".join(f"[{TOOL_SOURCE[n]}]\n{t}" for (n, a, t, m, e) in results)
    else:
        context = "(no information sources were selected for this question)"

    convo = ""
    prior = [m for m in history if m.get("role") in ("user", "assistant")][:-1][-4:]
    if prior:
        convo = ("Recent conversation:\n"
                 + "\n".join(f"{m['role']}: {m.get('content', '')}" for m in prior)
                 + "\n\n")

    return (f"{convo}Recruiter question: {question}\n\n"
            f"Retrieved information:\n{context}\n\n"
            "Answer the question using only the retrieved information above.")


def run(conversation_history: list, user_message: str,
        session_id: str = "local") -> tuple[str, list, list]:
    """
    Main agent turn.

    Scores all tools, runs every tool above the threshold concurrently, and
    synthesizes one grounded answer from the gathered context.

    Returns (answer_text, updated_conversation_history, tool_trajectory), where
    tool_trajectory is a list of
        {"tool", "args", "result_preview", "score"}
    for each tool that actually ran. The full per-tool probability vector (all
    four tools, whether or not they ran) is available via get_last_tool_scores().

    session_id labels this turn in the telemetry log so one recruiter's
    conversation can be read back as a thread.
    """
    global _LAST_TOOL_SCORES

    conversation_history.append({"role": "user", "content": user_message})

    with telemetry.turn(user_message, session_id=session_id) as rec:
        # 1. Score every tool (one call). 2. Select tools above the threshold.
        _LAST_TOOL_SCORES, selected, scores = select_tools(user_message, conversation_history)

        # 3. Run the selected tools concurrently.
        results = _run_tools_concurrently(selected)

        # 3b. Result-based escalation: if we ran tools but they ALL came back
        # empty, the router likely missed — run the REMAINING tools concurrently
        # and add whatever they retrieve. (Skipped when nothing was selected:
        # that is an out-of-scope question we intend to refuse, not a miss.)
        escalated = False
        if (config.TOOL_ESCALATE_ON_EMPTY and results
                and all(empty for (_n, _a, _t, _m, empty) in results)):
            escalated = True
            chosen = {n for (n, _a, _t, _m, _e) in results}
            rest = [(n, _args_for(n, scores[n], user_message))
                    for n in TOOL_NAMES if n not in chosen]
            results.extend(_run_tools_concurrently(rest))

        # Deterministic order by source precedence (project last-word etc.).
        results.sort(key=lambda r: SOURCE_ORDER.index(TOOL_SOURCE[r[0]]))

        _set_retrieval_meta(results)

        # 4. Synthesize one answer from all gathered context.
        answer = _synthesize(user_message, conversation_history, results)

        if rec is not None:
            meta = tools_module.get_last_retrieval_meta()
            rec.answer = answer
            rec.tools_selected = [n for (n, _a, _t, _m, _e) in results]
            rec.tool_scores = dict(_LAST_TOOL_SCORES)
            rec.route = meta.get("route")
            rec.n_chunks = len(meta.get("chunks") or [])
            rec.escalated = escalated

    conversation_history.append({"role": "assistant", "content": answer})

    trajectory = [{
        "tool": n,
        "args": a,
        "result_preview": (t or "")[:300],
        "score": _LAST_TOOL_SCORES[TOOL_SOURCE[n]],
    } for (n, a, t, m, e) in results]

    return answer, conversation_history, trajectory


class StreamingTurn:
    """One recruiter turn whose answer is streamed as the model writes it.

    Iterate it to get answer fragments; after it is exhausted, `answer`,
    `history` and `trajectory` hold exactly what run() would have returned.

    It is a class rather than a plain generator because a turn produces four
    things and a generator can only yield one of them. Streamlit's
    st.write_stream() consumes any iterable and returns the joined text, so the
    page renders the fragments and reads the rest off the object afterwards.

    Everything before synthesis — routing, tool execution, escalation — is
    identical to run() and is NOT streamed: it produces no text, only latency.
    The stream begins at the first synthesized token, which is the first moment
    there is anything to show.
    """

    def __init__(self, conversation_history: list, user_message: str,
                 session_id: str = "local"):
        self._history = conversation_history
        self._question = user_message
        self._session_id = session_id
        self.answer = ""
        self.history = conversation_history
        self.trajectory: list = []

    def __iter__(self):
        global _LAST_TOOL_SCORES

        history = self._history
        question = self._question
        history.append({"role": "user", "content": question})

        # The telemetry context stays open across the whole stream so the
        # synthesis call's tokens and cost land in this turn's record. That
        # requires the iterator to be consumed to completion, which
        # st.write_stream does.
        with telemetry.turn(question, session_id=self._session_id) as rec:
            _LAST_TOOL_SCORES, selected, scores = select_tools(question, history)
            results = _run_tools_concurrently(selected)

            escalated = False
            if (config.TOOL_ESCALATE_ON_EMPTY and results
                    and all(empty for (_n, _a, _t, _m, empty) in results)):
                escalated = True
                chosen = {n for (n, _a, _t, _m, _e) in results}
                rest = [(n, _args_for(n, scores[n], question))
                        for n in TOOL_NAMES if n not in chosen]
                results.extend(_run_tools_concurrently(rest))

            results.sort(key=lambda r: SOURCE_ORDER.index(TOOL_SOURCE[r[0]]))
            _set_retrieval_meta(results)

            prompt = _synthesis_prompt(question, history, results)
            pieces = []
            for piece in _stream_without_preamble(llm.complete_stream(
                    prompt, system=SYNTHESIS_SYSTEM, max_tokens=AGENT_MAX_TOKENS,
                    model=llm.agent_model, role="synthesis")):
                pieces.append(piece)
                yield piece

            self.answer = "".join(pieces).strip()

            if rec is not None:
                meta = tools_module.get_last_retrieval_meta()
                rec.answer = self.answer
                rec.tools_selected = [n for (n, _a, _t, _m, _e) in results]
                rec.tool_scores = dict(_LAST_TOOL_SCORES)
                rec.route = meta.get("route")
                rec.n_chunks = len(meta.get("chunks") or [])
                rec.escalated = escalated

        history.append({"role": "assistant", "content": self.answer})
        self.history = history
        self.trajectory = [{
            "tool": n,
            "args": a,
            "result_preview": (t or "")[:300],
            "score": _LAST_TOOL_SCORES[TOOL_SOURCE[n]],
        } for (n, a, t, m, e) in results]


def run_streaming(conversation_history: list, user_message: str,
                  session_id: str = "local") -> StreamingTurn:
    """Streaming counterpart to run(), for the recruiter chat.

    run() stays the buffered one-shot call: the evaluation harness wants the
    finished answer and nothing else, and streaming into it would only add a
    join.
    """
    return StreamingTurn(conversation_history, user_message, session_id)
