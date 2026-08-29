"""
tool_router.py — Probabilistic tool selection.

Instead of the LLM picking one tool, a single scoring call rates EVERY tool's
certainty (0.0–1.0) that it is needed for the question, and supplies the argument
to call it with. The agent then runs every tool whose score clears a threshold
(see settings.TOOL_SELECT_THRESHOLD) — so a close call fires more than one tool —
concurrently, and synthesizes one answer from all the gathered context. One
scoring pass; the scores are reused, never recomputed.
"""

from __future__ import annotations

import json
import re

# Tool name -> short "source" label used across the evaluator + report vocabulary
# (expected_tool / actual_tool are already structured/skill/docs/project).
TOOL_SOURCE = {
    "get_structured_data": "structured",
    "get_skill_proficiency": "skill",
    "search_documents": "docs",
    "search_project": "project",
}
SOURCE_ORDER = ["structured", "skill", "docs", "project"]
TOOL_NAMES = list(TOOL_SOURCE.keys())

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)
_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)

_STRUCTURED_FIELDS = (
    "full_name, email_address, country_code, phone_number, linkedin, github, "
    "education, years_of_experience, current_role, desired_job_title, "
    "job_description, monthly_salary_expectation, preferred_location, "
    "availability, work_type, open_to_relocation"
)

ROUTER_SYSTEM = f"""You route a recruiter's question to the right information sources.

There are FOUR tools. For EACH tool, output an INDEPENDENT relevance score from
0.0 to 1.0 — the probability that this tool is needed to help answer the question.
Scores are independent (they need NOT sum to 1): several tools can be high when a
question needs several, and ALL can be low for an out-of-scope question. Also give
the argument to call each tool with.

SCORING — use the FULL range, do not snap to 0/1:
- ~1.0  this tool is clearly required.
- ~0.5-0.8  this tool is plausibly useful / likely part of the answer.
- ~0.2-0.4  this tool MIGHT hold relevant material — when unsure, prefer ~0.3 over 0.0.
- 0.0  ONLY when the tool is clearly irrelevant. Reserve a hard 0.0 for tools that
  cannot possibly help. It is much worse to miss the right tool than to give a
  borderline tool a small score, so when a candidate question is not obviously a
  fixed field, give search_documents at least ~0.3.

THE FOUR TOOLS:
- get_structured_data (source "structured"): ONLY the verified fixed fields:
  {_STRUCTURED_FIELDS}. Use for direct lookups of those exact fields (contact info,
  the degree/field/institution/year/GPA, salary, availability, work type, etc.).
  It does NOT hold projects, achievements, coursework, a thesis, tools used, or any
  narrative — those live in the documents. arg "field".
- get_skill_proficiency (source "skill"): the evidence for how good / strong /
  experienced the candidate is in ONE SPECIFIC named skill or technology (e.g.
  "how good is she at Python?", "rate their AWS"). It is per-skill DEPTH, not a
  way to enumerate skills. arg "skill" (the one skill; "" only to list assessed skills).
- search_documents (source "docs"): semantic search over the CANDIDATE's own
  documents (CV, certificates, recommendations). This is the DEFAULT for anything
  about the candidate that is not a single fixed field. Score it high for:
  * ENUMERATION / lists — "what programming languages / databases / tools /
    frameworks / certifications does the candidate know or use?" (NOT skill, NOT
    structured).
  * PROJECTS, detailed experience, responsibilities, achievements, publications.
  * EDUCATION specifics beyond the degree field — thesis, coursework, honors,
    awards, Dean's list (structured only has the degree/field/school/year/GPA).
  * COMPARISON / JUDGMENT / FIT — "compare academic vs professional experience",
    "is she overqualified", "good fit for X role", "unique combination of skills",
    "strongest skills", "why should I hire", "summarize the candidate".
  arg "query".
- search_project (source "project"): search THIS system's own documentation — how
  the app / agent works: architecture, the RAG pipeline, models, reranker, the
  skill scorer, evaluation, deployment. Includes SECOND-PERSON questions about how
  YOU operate ("how do you retrieve?", "what model are you?"). arg "query".

DISAMBIGUATION:
- Candidate's profile -> structured / skill / docs. How the SYSTEM or you (the
  agent) works -> project. "you/your" about the candidate's OWN profile ("your
  skills", "your experience", "what did you build") is still the candidate tools.
- "How good at <one skill>?" -> skill (high) and usually docs (~0.4). "What skills
  / languages / tools does she have?" -> docs (high), NOT skill.
- A named skill NOT necessarily assessed still gets docs a solid score as fallback.
- Out-of-scope / personal (blood type, politics, religion, marital status, credit
  score — anything not professional) -> ALL tools 0.0.

EXAMPLES (question -> the four scores structured/skill/docs/project):
- "What is the candidate's email?"                    -> 1.0 / 0.0 / 0.1 / 0.0
- "Does the candidate have a Master's degree?"        -> 0.9 / 0.0 / 0.2 / 0.0
- "How proficient is she at Python?"                  -> 0.0 / 1.0 / 0.4 / 0.0
- "What programming languages does the candidate know?"-> 0.1 / 0.2 / 0.9 / 0.0
- "What databases has the candidate worked with?"     -> 0.0 / 0.1 / 0.9 / 0.0
- "What was the candidate's thesis about?"            -> 0.1 / 0.0 / 0.9 / 0.0
- "Did the candidate receive academic honors?"        -> 0.2 / 0.0 / 0.8 / 0.0
- "Compare her academic and professional experience." -> 0.4 / 0.1 / 0.9 / 0.0
- "What are the candidate's strongest skills?"        -> 0.1 / 0.5 / 0.8 / 0.0
- "Is the candidate overqualified for a junior role?" -> 0.2 / 0.2 / 0.9 / 0.0
- "Summarize why I should consider this candidate."   -> 0.2 / 0.2 / 0.9 / 0.0
- "What reranker do you use?"                         -> 0.0 / 0.0 / 0.0 / 1.0
- "What is the candidate's blood type?"               -> 0.0 / 0.0 / 0.0 / 0.0

Respond with ONLY a JSON object, no prose, exactly this shape:
{{
  "get_structured_data": {{"score": <0..1>, "field": "<field or empty>"}},
  "get_skill_proficiency": {{"score": <0..1>, "skill": "<skill or empty>"}},
  "search_documents": {{"score": <0..1>, "query": "<search query>"}},
  "search_project": {{"score": <0..1>, "query": "<search query>"}}
}}"""


def _clamp(x) -> float:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, v))


def score_tools(llm, question: str, history: list | None = None) -> dict:
    """Score all four tools for a question.

    Returns {tool_name: {"score": float, **args}} for every tool. A tool the
    model omitted (or a malformed response) defaults to score 0.0.
    """
    convo = ""
    if history:
        recent = [m for m in history if m.get("role") in ("user", "assistant")][-4:]
        if recent:
            convo = ("Recent conversation:\n"
                     + "\n".join(f"{m['role']}: {m.get('content', '')}" for m in recent)
                     + "\n\n")
    prompt = (f"{convo}Recruiter question: {question}\n\n"
              "Score each tool as instructed and return only the JSON object.")

    raw = _THINK_RE.sub("", llm.complete(prompt, system=ROUTER_SYSTEM, max_tokens=400)).strip()

    data = {}
    try:
        data = json.loads(raw)
    except Exception:
        m = _JSON_RE.search(raw)
        if m:
            try:
                data = json.loads(m.group())
            except Exception:
                data = {}

    out = {}
    for name in TOOL_NAMES:
        entry = data.get(name)
        if not isinstance(entry, dict):
            entry = {}
        entry["score"] = _clamp(entry.get("score", 0.0))
        out[name] = entry
    return out
