from rag.retriever import retrieve
from store.structured import (
    get_field,
    get_skill_evidence,
    get_skill_evidence_for,
)

CANDIDATE_ID = "candidate_001"  # later: dynamic per candidate
PROJECT_ID = "project_kb"       # separate collection holding the project overview

# Store the last retrieval metadata for evaluation access
_last_retrieval_meta = {}

# -- Tool schemas (provider-neutral; see agent/llm.py) ----------------------
# Each tool is {"name", "description", "parameters": <JSON schema>}. The LLM
# client converts this to the active provider's format (Anthropic input_schema
# or Ollama function spec) at call time.

TOOL_SCHEMAS = [
    {
        "name": "get_structured_data",
        "description": (
            "Get fixed, guaranteed-accurate candidate information. "
            "ONLY use this tool for the following fields:\n"
            "  Personal: full_name, email_address, country_code, phone_number, linkedin, github\n"
            "  Education: education (returns all degrees, fields of study, institutions, and GPAs)\n"
            "  Experience: years_of_experience, current_role, desired_job_title, job_description\n"
            "  Preferences: monthly_salary_expectation, preferred_location, availability, work_type, open_to_relocation\n"
            "If the question does not match one of these fields, "
            "use search_documents instead."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "field": {
                    "type": "string",
                    "description": (
                        "One of: full_name, email_address, country_code, "
                        "phone_number, linkedin, github, education, "
                        "years_of_experience, current_role, desired_job_title, "
                        "job_description, monthly_salary_expectation, "
                        "preferred_location, availability, work_type, open_to_relocation"
                    )
                }
            },
            "required": ["field"]
        }
    },
    {
        "name": "get_skill_proficiency",
        "description": (
            "Get the concrete EVIDENCE the candidate's documents contain for a "
            "skill — the specific passages a retrieval model surfaced for it. "
            "This evidence was curated when the candidate set up their profile "
            "and is the fast, grounded source for skill questions (no re-search "
            "needed).\n"
            "USE THIS for any question about HOW GOOD / HOW STRONG / HOW PROFICIENT / "
            "HOW SKILLED / HOW EXPERIENCED the candidate is in a specific technology, "
            "tool, or skill, or to characterize/compare their skills (e.g. 'How "
            "good is she at Python?', 'How strong is their AWS?', 'What are their "
            "key skills?'). Pass the skill name; omit it to list every assessed "
            "skill. If the skill was not assessed, this tool says so — then fall "
            "back to search_documents.\n"
            "IMPORTANT: this tool returns EVIDENCE, not a numeric rating. Describe "
            "what the evidence shows (projects, scope, responsibilities) in your "
            "own words. Do NOT invent or state a 1-5 score, star rating, or "
            "percentage — no such score is available to you."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "skill": {
                    "type": "string",
                    "description": (
                        "The skill/technology to get the evidence for "
                        "(e.g. 'Python', 'AWS'). Leave empty to list all assessed "
                        "skills."
                    )
                }
            },
            "required": []
        }
    },
    {
        "name": "search_documents",
        "description": (
            "Search the candidate's uploaded documents (CV, grades, certificates). "
            "Use this for ANY question ABOUT THE CANDIDATE that is not covered "
            "by get_structured_data or get_skill_proficiency — including projects, "
            "detailed experience, what they did with a technology, achievements, "
            "certifications, and more. Also use this as a fallback when a skill was "
            "not among the assessed proficiencies. Do NOT use this for questions "
            "about how THIS app/system was built — use search_project for that."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The question or topic to search for"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "search_project",
        "description": (
            "Search documentation about THIS software project / system itself AND "
            "about how YOU, the AI agent, work. Covers: the architecture, "
            "technology stack, the RAG pipeline (routing, query expansion, hybrid "
            "BM25 + vector fusion, RRF, reranking), the trained skill-proficiency "
            "model, the evaluation suite, deployment, security, and design "
            "decisions.\n"
            "USE THIS for two kinds of questions:\n"
            "  (1) Questions about the project/system/app/tool itself — e.g. 'How "
            "does the RAG pipeline work?', 'What reranker does this project use?', "
            "'How is skill proficiency estimated?', 'What is this system?'.\n"
            "  (2) SECOND-PERSON questions addressed to you, the agent, about how "
            "you operate or were built — e.g. 'How do you work?', 'How were you "
            "built?', 'What model are you / powers you?', 'What reranker/embedder "
            "do you use?', 'How do you decide which tool to call?', 'How do you "
            "retrieve documents?', 'How do you score skills?', 'How were you "
            "evaluated?'. Here 'you' means the agent/system, so the answer comes "
            "from this tool.\n"
            "Do NOT use this for questions about the CANDIDATE's own professional "
            "profile, even when phrased with 'you/your' — 'your name', 'your "
            "skills', 'your experience', 'what did you build/do' refer to the "
            "candidate and use get_structured_data, get_skill_proficiency, or "
            "search_documents. The rule: questions about how the agent/system "
            "*operates or is engineered* → search_project; questions about the "
            "*person being represented* → the candidate tools."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The question or topic about the project to search for"
                }
            },
            "required": ["query"]
        }
    }
]

# -- Tool execution functions ------------------------------------------------


def search_documents(**kwargs) -> str:
    global _last_retrieval_meta
    # Accept any argument name the LLM uses (query, field, etc.)
    query = kwargs.get("query", next(iter(kwargs.values()), ""))
    # Auto-recover if the LLM passes a dict instead of a string
    if isinstance(query, dict):
        query = query.get("query", query.get("description", str(query)))
    result = retrieve(str(query), CANDIDATE_ID)
    chunks = result["chunks"]
    # Store retrieval metadata for evaluation
    _last_retrieval_meta = {
        "route": result["route"],
        "expanded_queries": result["expanded_queries"],
        "chunks": chunks,
        "fused_pool": result.get("fused_pool"),
    }
    if not chunks:
        return "No relevant information found in documents."
    return "\n\n".join(chunks)


def search_project(**kwargs) -> str:
    """RAG over the project-overview collection (the app/system itself), kept
    separate from the candidate's documents. Mirrors search_documents but targets
    PROJECT_ID, and records retrieval metadata the same way for evaluation."""
    global _last_retrieval_meta
    query = kwargs.get("query", next(iter(kwargs.values()), ""))
    if isinstance(query, dict):
        query = query.get("query", query.get("description", str(query)))
    result = retrieve(str(query), PROJECT_ID)
    chunks = result["chunks"]
    _last_retrieval_meta = {
        "route": result["route"],
        "expanded_queries": result["expanded_queries"],
        "chunks": chunks,
        "fused_pool": result.get("fused_pool"),
    }
    if not chunks:
        return "No relevant information found about the project."
    return "\n\n".join(chunks)


def get_structured_data(**kwargs) -> str:
    # Accept any argument name the LLM uses (field, query, etc.)
    field = kwargs.get("field", next(iter(kwargs.values()), ""))
    # Auto-recover if the LLM passes a dict instead of a string
    if isinstance(field, dict):
        raw = field.get("field", field.get("description", str(field)))
        field = raw.split(":")[0].strip()
    value = get_field(str(field))
    return f"{field}: {value}"


def get_skill_proficiency(**kwargs) -> str:
    """Return the curated document EVIDENCE for a candidate skill (read from the
    structured store, where it was saved at profile-setup time).

    Deliberately returns evidence only — never the trained model's 1-5 level,
    which is candidate-private and not persisted. The agent grounds its answer in
    these passages and describes the skill qualitatively.
    """
    # Accept any argument name the LLM uses (skill, query, field, ...)
    skill = kwargs.get("skill", next(iter(kwargs.values()), ""))
    if isinstance(skill, dict):
        skill = skill.get("skill", skill.get("description", str(skill)))
    skill = str(skill).strip()

    evidence = get_skill_evidence()
    if not evidence:
        return ("No curated skill evidence is available for this candidate. "
                "Use search_documents to look for skill evidence in the documents.")

    # No specific skill → list everything that was assessed
    if not skill:
        listed = ", ".join(e["skill"] for e in evidence)
        return ("Assessed skills (each has supporting evidence from the "
                f"documents): {listed}.\n"
                "Ask about any one of them to see the specific evidence, or use "
                "search_documents for more detail.")

    entry = get_skill_evidence_for(skill)
    if entry is None:
        listed = ", ".join(e["skill"] for e in evidence)
        return (f"'{skill}' was not among the candidate's assessed skills "
                f"(assessed: {listed}). Use search_documents to check the documents directly.")

    chunks = entry.get("chunks", [])
    if not chunks:
        return (f"'{entry['skill']}' was assessed but no supporting passages were "
                "retrieved for it. Use search_documents to check the documents directly.")

    lines = [
        f"Document evidence for '{entry['skill']}' (describe what it shows in your "
        "own words; do not state a numeric rating):",
    ]
    for c in chunks[:3]:
        preview = c[:300] + ("…" if len(c) > 300 else "")
        lines.append(f"- {preview}")
    return "\n".join(lines)


def get_last_retrieval_meta() -> dict:
    """Return the metadata from the last search_documents call."""
    return _last_retrieval_meta.copy()


# -- Dispatcher --------------------------------------------------------------

TOOL_FUNCTIONS = {
    "search_documents": search_documents,
    "search_project": search_project,
    "get_structured_data": get_structured_data,
    "get_skill_proficiency": get_skill_proficiency,
}


def execute_tool(name: str, arguments: dict) -> str:
    func = TOOL_FUNCTIONS.get(name)
    if not func:
        return f"Unknown tool: {name}"
    return func(**arguments)
